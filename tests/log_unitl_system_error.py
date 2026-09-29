import argparse
import asyncio
import logging
from pathlib import Path
import sys

PROJECT_SOURCE_DIRECTORY = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PROJECT_SOURCE_DIRECTORY))

from soniccontrol.remote_controller import RemoteController
from soniccontrol.data_capturing.experiment import ExperimentMetaData
from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import SystemState
from soniccontrol.updater import Updater
from soniccontrol.utils.events import Event


POLL_INTERVAL_SECONDS = 0.2
DAMAGE_SETTLE_SECONDS = 5
FILTERED_LOG_SOURCE = "rp2040_transducer.cpp:246"


class FirmwareSourceFilter(logging.Filter):
	def filter(self, record: logging.LogRecord) -> bool:
		return FILTERED_LOG_SOURCE not in record.getMessage()


async def main(serial_port: str, log_directory: Path) -> None:
	print(f"Connecting to {serial_port}...")
	controller = await RemoteController.connect_via_serial(
		serial_port,
		log_path=log_directory,
	)
	for handler in controller._logger.handlers:
		handler.addFilter(FirmwareSourceFilter())

	damage_detected = asyncio.Event()

	def on_update(event: Event) -> None:
		system_state = event.data["status"].get(EFieldName.SYSTEM_STATE)
		if system_state is SystemState.COMPONENT_DAMAGED:
			damage_detected.set()

	controller._updater.subscribe(Updater.UPDATE_EVENT, on_update)
	capture = controller.capture_experiment(
		log_directory,
		ExperimentMetaData(
			experiment_name="system_error_monitor",
			authors=["system_error_monitor"],
			transducer_id="unknown",
			add_on_id="unknown",
			connector_type="unknown",
			medium="unknown",
		),
	)

	try:
		await capture.start_capture()
		print(f"Capturing experiment data and logs in {log_directory}.")
		await damage_detected.wait()
		print("System state is damaged; capturing for five more seconds.")
		await asyncio.sleep(DAMAGE_SETTLE_SECONDS)
	finally:
		await capture.end_capture()
		controller._updater.unsubscribe(Updater.UPDATE_EVENT, on_update)
		await controller.disconnect()
		print("Capture complete.")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Record device logs until the system state becomes damaged."
	)
	parser.add_argument("serial_port", help="Serial port, for example COM6 or /dev/ttyUSB0")
	parser.add_argument(
		"--log-directory",
		type=Path,
		default=Path("output/system_error_logs"),
		help="Directory for the RemoteController connection log",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = parse_args()
	asyncio.run(main(args.serial_port, args.log_directory))
