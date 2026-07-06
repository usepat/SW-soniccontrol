import abc
import asyncio
import base64
from datetime import datetime
from enum import Enum
import os
import shutil
import tempfile
os.environ.setdefault("PYPPETEER_CHROMIUM_REVISION", "1181217")
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import attrs
import numpy as np
from sonic_protocol.protocol import protocol_list
from sonic_protocol.groups import GroupId, get_spec
from sonic_protocol.schema import (
    CommandContract,
    ConverterType,
    DeviceParamConstantType,
    DeviceType,
    ProtocolType,
    Timestamp,
    Version,
)
import sonic_protocol
from sonic_protocol.user_manual_compiler.command_example_utils import (
    deduce_answer_example_for_contract,
    deduce_single_command_example_for_contract,
)
from sonic_protocol.user_manual_compiler.manual_compiler import ManualCompiler


import importlib.resources as rs
import jinja2
from pyppeteer import launch
from pyppeteer import chromium_downloader as cd


@dataclass
class GroupNode:
    id: GroupId
    title: str
    description: str
    order: int
    depth: int
    children: List["GroupNode"] = field(default_factory=list)
    commands: List["CommandContract"] = field(default_factory=list)


def add_wbr_before_underscore(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("_", "<wbr>_")


def load_asset_data_uri(asset_path: Path) -> str | None:
    if not asset_path.exists():
        return None

    suffix = asset_path.suffix.lower()
    mime_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
    }.get(suffix)

    if mime_type is None:
        return None

    return f"data:{mime_type};base64,{base64.b64encode(asset_path.read_bytes()).decode('ascii')}"


def device_name_to_label(value: object) -> str:
    """Convert device type identifiers to a human-friendly label.

    Replaces underscores with spaces and converts the result to
    Title Case (capitalize the first letter of each word).
    """
    text = "" if value is None else str(value)
    return text.replace("_", " ").strip().upper()


def format_constraint_value(value: object, consts: object) -> str:
    if isinstance(value, DeviceParamConstantType):
        value = getattr(consts, value.value)

    if isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, float):
        return f"{value:g}"

    return str(value)


def should_include_command_in_manual(
    command_contract: CommandContract,
    *,
    include_text: bool,
    is_postman_device: bool,
) -> bool:
    if not include_text and command_contract.group_id == GroupId("logging"):
        return False

    if not is_postman_device:
        command_name = getattr(command_contract.code, "name", "")
        command_tags = getattr(command_contract, "tags", [])
        if command_name == "GET_POSTMAN_UPDATE" or "postman" in command_tags:
            return False

    return True

def build_group_tree(
    command_contracts: List["CommandContract"],
    is_release: bool,
    is_admin: bool,
) -> List[GroupNode]:
    """
    Returns root nodes. Each node has children + commands.
    Assumes each contract has exactly one group_id (leaf).
    """
    # bucket commands by leaf group
    by_group: Dict[GroupId, List["CommandContract"]] = defaultdict(list)
    leaf_groups: set[GroupId] = set()

    for c in command_contracts:
        if (is_release and not c.is_release) or (not is_admin and c.is_admin_command):
            continue
        gid: GroupId = getattr(c, "group_id", GroupId("misc")) or GroupId("misc")
        by_group[gid].append(c)
        leaf_groups.add(gid)

    # compute closure: include ancestors
    needed: set[GroupId] = set()
    for gid in leaf_groups:
        cur: Optional[GroupId] = gid
        while cur is not None:
            needed.add(cur)
            spec = get_spec(cur)
            cur = spec.parent

    # build children map
    children_map: Dict[Optional[GroupId], List[GroupId]] = defaultdict(list)
    for gid in needed:
        spec = get_spec(gid)
        parent = spec.parent
        children_map[parent].append(gid)

    def sort_key(gid: GroupId):
        spec = get_spec(gid)
        return (spec.order, spec.title.lower(), str(gid))

    for parent, kids in list(children_map.items()):
        kids.sort(key=sort_key)

    # build nodes recursively
    def make_node(gid: GroupId, depth: int) -> GroupNode:
        spec = get_spec(gid)
        node = GroupNode(
            id=gid,
            title=spec.title,
            description=spec.description,
            order=spec.order,
            depth=depth,
        )
        # attach commands at the leaf group
        cmds = by_group.get(gid, [])
        # stable command ordering (by code value then name)
        cmds.sort(key=lambda c: (int(getattr(c.code, "value", 0)), getattr(c.code, "name", "")))
        node.commands = cmds

        # children
        for child_gid in children_map.get(gid, []):
            child_spec = get_spec(child_gid)
            if is_release and not child_spec.is_release:
                continue
            node.children.append(make_node(child_gid, depth + 1))
        return node

    roots: List[GroupNode] = []
    for root_gid in children_map.get(None, []):
        root_spec = get_spec(root_gid)
        if is_release and not root_spec.is_release:
            continue
        roots.append(make_node(root_gid, depth=0))

    return roots




class HtmlManualCompiler(ManualCompiler):
    def compile_manual_for_specific_device(self, device_type: DeviceType, protocol_version: Version, is_release: bool = True, is_admin: bool = False, mode: str = "both") -> str:
        try:
            protocol = protocol_list.build_protocol_for(ProtocolType(protocol_version, device_type, is_release))
        except Exception as e:
            return "Error constructing manual: " + str(e)

        # mode: "both" | "modbus" | "text"
        include_modbus = mode in ("modbus", "both")
        include_text = mode in ("text", "both")
        is_postman_device = device_type == DeviceType.POSTMAN
        
        error_code_begin = 20000 # all command codes greater than 20000 are error codes
        pure_command_contracts = [
            elem
            for elem in protocol.command_contracts.values()
            if elem.command_def is not None
            and should_include_command_in_manual(
                elem,
                include_text=include_text,
                is_postman_device=is_postman_device,
            )
        ]
        command_groups = build_group_tree(pure_command_contracts, is_release=is_release, is_admin=is_admin)
        error_codes = [ code for code in protocol.command_code_cls if code >= error_code_begin ]
        notification_messages = [
            elem
            for elem in protocol.command_contracts.values()
            if include_text and elem.command_def is None and elem.code.value < error_code_begin
        ]
        enum_classes = [ elem for elem in protocol.custom_data_types.values() if issubclass(elem, Enum) ]

        template_path = rs.files(sonic_protocol).joinpath("user_manual_compiler/jinja_templates")
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_path)))
        environment.globals.update({ 
            "any": any,
            "enumerate": enumerate,
            "issubclass": issubclass,
            "isinstance": isinstance,
            "now": datetime.now,
            "bool": bool,
            "int": int,
            "str": str,
            "float": float,
            "np": np, # needed for np.uint8, etc.
            "ConverterType": ConverterType,
            "Version": Version,
            "Enum": Enum,
            "Timestamp": Timestamp,
            "protocol_constants": attrs.asdict(protocol.consts), # FIXME: It would be better to pass this as render variable, but I am lazy
            "protocol_consts": protocol.consts,
            "deduce_single_command_example_for_contract": deduce_single_command_example_for_contract,
            "deduce_answer_command_example_for_contract": deduce_answer_example_for_contract,
            "device_name_to_label": device_name_to_label,
            "format_constraint_value": format_constraint_value,
            "anchor_group": lambda gid: f"group-{str(gid).replace('.', '-')}",
            "anchor_cmd": lambda code: f"cmd-{int(code.value)}",
            "add_wbr_before_underscore": add_wbr_before_underscore,
        }) # export functions and classes to jinja environment. So we can use them inside the templates

        template = environment.get_template("index.j2")
        device_type_name = device_type.value
        protocol_version_str = str(protocol_version)
        release_type = "Release" if is_release else "Development"
        build_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cover_date_str = datetime.now().strftime("%d.%m.%Y")
        if mode == "text":
            cover_reference_title = "Sonic Text Protocol Reference"
        elif mode == "modbus":
            cover_reference_title = "Sonic MODBUS Protocol Reference"
        else:
            cover_reference_title = "Sonic Protocol Reference"

        repo_root = Path(__file__).resolve().parents[3]
        gui_resources = repo_root / "src" / "soniccontrol_gui" / "resources"
        usepat_logo_src = load_asset_data_uri(
            gui_resources / "pictures" / "usepat_neu-4c-mSL.png"
        )
        footer_image_src = load_asset_data_uri(
            gui_resources / "icons" / "thumbnail_usePAT_Briefpapier_Adressblock_end 1.jpg"
        )
        qtype_cond_light_src = load_asset_data_uri(
            gui_resources / "fonts" / "QTypeOT-CondLight.otf"
        )
        qtype_cond_book_src = load_asset_data_uri(
            gui_resources / "fonts" / "QTypeOT-CondBook.otf"
        )
        qtype_cond_medium_src = load_asset_data_uri(
            gui_resources / "fonts" / "QTypeOT-CondMedium.otf"
        )
        qtype_cond_bold_src = load_asset_data_uri(
            gui_resources / "fonts" / "QTypeOT-CondBold.otf"
        )

        content = template.render(
            command_groups=command_groups,  
            pure_command_contracts=pure_command_contracts, 
            error_codes=error_codes,
            notification_messages=notification_messages,
            enum_classes=enum_classes,
            include_modbus=include_modbus,
            include_text=include_text,
            is_postman_device=is_postman_device,
            device_type_name=device_type_name,
            protocol_version_str=protocol_version_str,
            release_type=release_type,
            build_date_str=build_date_str,
            cover_date_str=cover_date_str,
            cover_reference_title=cover_reference_title,
            usepat_logo_src=usepat_logo_src,
            footer_image_src=footer_image_src,
            qtype_cond_light_src=qtype_cond_light_src,
            qtype_cond_book_src=qtype_cond_book_src,
            qtype_cond_medium_src=qtype_cond_medium_src,
            qtype_cond_bold_src=qtype_cond_bold_src,
        )

        return content 
    

def main():
    manual_compiler = HtmlManualCompiler()

    Path("./output").mkdir(exist_ok=True, parents=True)

    device_type = DeviceType.MVP_WORKER
    protocol_version = Version(3, 0, 0)
    is_release = True

    def build_pdf_path(basename: str) -> str:
        release_mode = "release" if is_release else "development"
        device_label = str(device_type.value).lower().replace(" ", "_")
        version_label = str(protocol_version).replace(" ", "_")
        return f"./output/{basename}_{device_label}_{version_label}_{release_mode}.pdf"

    # Produce two documents: one for the text-based API and one for MODBUS
    targets = (("text", "manual_text"), ("modbus", "manual_modbus"), ("both", "manual"))
    for mode, basename in targets:
        manual = manual_compiler.compile_manual_for_specific_device(
            device_type,
            protocol_version,
            is_release,
            mode=mode,
        )

        html_path = f"./output/{basename}.html"
        with open(html_path, "w", encoding="utf-8") as file:
            file.write(manual)
    
    def find_browser() -> str | None:
        # 1) Explicit override
        exe = os.getenv("PYPPETEER_EXECUTABLE_PATH")
        if exe and Path(exe).exists():
            return exe

        # 2) PATH candidates (Linux/macOS, sometimes Windows)
        for name in ("google-chrome-stable", "google-chrome", "msedge", "chromium", "chromium-browser"):
            p = shutil.which(name)
            if p:
                return p

        # 3) Common Windows locations (covers most installs)
        if os.name == "nt":
            candidates = [
                Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
                Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft/Edge/Application/msedge.exe",
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft/Edge/Application/msedge.exe",
            ]
            for c in candidates:
                if c.exists():
                    return str(c)

        return None

    async def get_browser() -> tuple:
        exe = find_browser()
        if not exe:
            raise RuntimeError(
                "No system browser found. Install Google Chrome or Microsoft Edge, "
                "or set PYPPETEER_EXECUTABLE_PATH to the browser executable."
            )

        user_data_dir = tempfile.mkdtemp(prefix="pyppeteer-profile-")
        launch_args = [f"--user-data-dir={user_data_dir}"]

        if os.name != "nt":
            launch_args.extend(["--no-sandbox", "--disable-setuid-sandbox"])

        try:
            browser = await launch(
                executablePath=exe,
                headless=True,
                args=launch_args,
                autoClose=False,
                handleSIGINT=False,
                handleSIGTERM=False,
                handleSIGHUP=False,
            )
        except Exception:
            shutil.rmtree(user_data_dir, ignore_errors=True)
            raise

        return browser, user_data_dir

    def convert_html_to_pdf(html_path: str, pdf_path: str) -> None:
        async def _pdf():
            browser, user_data_dir = await get_browser()
            try:
                page = await browser.newPage()
                await page.goto("file://" + str(Path(html_path).absolute()), {"waitUntil": "networkidle0"})
                await page.waitForFunction("document.fonts && document.fonts.status === 'loaded'")
                await page.emulateMedia("print")
                await page.evaluate("window.updateTocPageNumbers && window.updateTocPageNumbers()")
                await page.waitForFunction(
                    """
                    () => {
                        const tocPages = Array.from(document.querySelectorAll('.toc-page[data-target]'));
                        if (tocPages.length === 0) {
                            return true;
                        }

                        return tocPages.every((element) => {
                            const pageNumber = element.getAttribute('data-page');
                            return pageNumber && pageNumber !== '?' && element.textContent.trim() !== 'p. ?';
                        });
                    }
                    """
                )

                client = page._client
                cdp_options = {
                    "printBackground": True,
                    "preferCSSPageSize": True,
                    "displayHeaderFooter": True,
                    "headerTemplate": "<div></div>",
                    "footerTemplate": """
                        <div style=\"width:100%; font-size:9px; color:#6b7280; padding:0 8mm 4mm; box-sizing:border-box; text-align:right; font-family:Arial, sans-serif;\">
                            page <span class=\"pageNumber\"></span> of <span class=\"totalPages\"></span>
                        </div>
                    """,
                    "marginTop": 0.4724,
                    "marginBottom": 0.7087,
                    "generateTaggedPDF": True,
                    "generateDocumentOutline": True,
                }
                result = await client.send("Page.printToPDF", cdp_options)
                Path(pdf_path).write_bytes(base64.b64decode(result["data"]))
            finally:
                await browser.close()
                shutil.rmtree(user_data_dir, ignore_errors=True)

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_pdf())
        finally:
            asyncio.set_event_loop(None)
            loop.close()

    for mode, basename in targets:
        html_path = f"./output/{basename}.html"
        pdf_path = build_pdf_path(basename)
        try:
            convert_html_to_pdf(html_path, pdf_path)
            print(f"Wrote {pdf_path}")
        except Exception as e:
            print(f"PDF conversion for {basename} skipped:", e)

if __name__ == "__main__":
    main()
