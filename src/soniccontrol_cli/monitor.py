from cmd import Cmd
import click
import asyncio

from soniccontrol import RemoteController
from sonic_protocol.user_manual_compiler.manual_compiler import MarkdownManualCompiler
from sonic_protocol.protocol import protocol
from soniccontrol_gui.utils.animator import Animator, DotAnimationSequence, load_animation

class Monitor(Cmd): 
    intro = """Welcome to the monitor. 
    Input 'help' to get the manual for the device and 
    input 'exit' to leave the monitor."""

    def __init__(self, remote_controller: RemoteController, event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()):
        super().__init__()
        self._remote_controller = remote_controller
        self._event_loop = event_loop

        assert (self._remote_controller._device)
        self._info = self._remote_controller._device.info
        device_type_str = click.style(self._info.device_type.value, fg="blue")
        hw_version_str = click.style(self._info.hardware_version, fg="yellow")
        self.prompt = device_type_str + click.style("@", fg="green") + hw_version_str + click.style(">>> ", fg="green")

        # decorate send_command with loading animation
        loading_message = "Waiting for answer"
        num_dots = 5
        animation = Animator(
            sequence=DotAnimationSequence(f"\r{loading_message}", num_dots=num_dots), 
            apply_on_target=lambda animation_frame_str: click.echo(animation_frame_str, nl=False), 
            frame_rate=5,
            done_callback=lambda: click.echo(f"\r{' ' * (len(loading_message) + num_dots)}\r", nl=False) # for deleting the loading string
        )
        animation_decorator = load_animation(
            animation, 
            num_repeats=-1
        )
        self._send_command = animation_decorator(self._remote_controller.send_command)

    def emptyline(self) -> bool:
        return False

    def do_help(self, arg: str) -> bool | None:
        manual_compiler = MarkdownManualCompiler(protocol)
        manual: str = manual_compiler.compile_manual_for_specific_device(self._info.device_type, self._info.protocol_version, self._info.is_release)
        click.echo_via_pager(manual)

    def do_exit(self, arg: str) -> bool | None:
        return True

    def _lint_output(self, output: str) -> str:
        tokens = output.split("#")
        colored_tokens = map(lambda s: click.style(s, fg="white"), tokens)
        colored_delimiter = click.style("#", fg="bright_cyan")
        return colored_delimiter.join(colored_tokens)

    def default(self, line: str):
        answer_str, _, answer_valid = self._event_loop.run_until_complete(self._send_command(line))
        if answer_valid:
            answer_colorized = self._lint_output(answer_str)
            click.echo(answer_colorized)
        else:
            click.secho(answer_str, err=True, fg="red")

    # We need to override onecmd, that is responsible for parsing the commands, 
    # because it propagates everything that starts with ? to do_help and ! to do_shell
    def onecmd(self, line: str) -> bool:
        if line.startswith("?") or line.startswith("!"):
            self.default(line)
            return False
        return super().onecmd(line)
    