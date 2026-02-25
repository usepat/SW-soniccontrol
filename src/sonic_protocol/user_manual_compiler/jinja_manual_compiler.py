import abc
from datetime import datetime
from enum import Enum
from pathlib import Path

import attrs
import numpy as np
from sonic_protocol.protocol import protocol_list
from sonic_protocol.schema import ConverterType, DeviceType, ProtocolType, Timestamp, Version
import sonic_protocol
from sonic_protocol.user_manual_compiler.manual_compiler import ManualCompiler


import importlib.resources as rs
import jinja2
import asyncio
from pyppeteer import launch


class HtmlManualCompiler(ManualCompiler):
    def compile_manual_for_specific_device(self, device_type: DeviceType, protocol_version: Version, is_release: bool = True, mode: str = "both") -> str:
        try:
            protocol = protocol_list.build_protocol_for(ProtocolType(protocol_version, device_type, is_release))
        except Exception as e:
            return "Error constructing manual: " + str(e)
        
        error_code_begin = 20000 # all command codes greater than 20000 are error codes
        pure_command_contracts = [ elem for elem in protocol.command_contracts.values() if elem.command_def is not None ]
        error_codes = [ code for code in protocol.command_code_cls if code >= error_code_begin ]
        notification_messages = [ elem for elem in protocol.command_contracts.values() if elem.command_def is None and elem.code.value < error_code_begin ]
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
            "protocol_constants": attrs.asdict(protocol.consts) # FIXME: It would be better to pass this as render variable, but I am lazy
        }) # export functions and classes to jinja environment. So we can use them inside the templates

        # mode: "both" | "modbus" | "text"
        include_modbus = mode in ("modbus", "both")
        include_text = mode in ("text", "both")

        template = environment.get_template("index.j2")
        content = template.render(
            pure_command_contracts=pure_command_contracts,
            error_codes=error_codes,
            notification_messages=notification_messages,
            enum_classes=enum_classes,
            include_modbus=include_modbus,
            include_text=include_text,
        )

        return content 
    

def main():
    manual_compiler = HtmlManualCompiler()

    Path("./output").mkdir(exist_ok=True, parents=True)

    # Produce two documents: one for the text-based API and one for MODBUS
    targets = (("text", "manual_text"), ("modbus", "manual_modbus"))
    for mode, basename in targets:
        manual = manual_compiler.compile_manual_for_specific_device(
            DeviceType.MVP_WORKER,
            Version(3, 0, 0),
            True,
            mode=mode,
        )

        html_path = f"./output/{basename}.html"
        pdf_path = f"./output/{basename}.pdf"
        with open(html_path, "w") as file:
            file.write(manual)

    def convert_html_to_pdf(html_path: str, pdf_path: str) -> None:
        async def _pdf():
            browser = await launch()
            page = await browser.newPage()
            await page.goto("file://" + str(Path(html_path).absolute()))
            await page.pdf({"path": str(pdf_path), "format": "A4"})
            await browser.close()

        asyncio.get_event_loop().run_until_complete(_pdf())

    for mode, basename in targets:
        html_path = f"./output/{basename}.html"
        pdf_path = f"./output/{basename}.pdf"
        try:
            convert_html_to_pdf(html_path, pdf_path)
            print(f"Wrote {pdf_path}")
        except Exception as e:
            print(f"PDF conversion for {basename} skipped:", e)

if __name__ == "__main__":
    main()
