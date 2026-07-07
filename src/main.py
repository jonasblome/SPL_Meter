import SPLMeter as spl
import argparse

parser = argparse.ArgumentParser(description="An SPL Meter.")
parser.add_argument("-s", "--simulate", type=str, help="Simulate audio input using a 16/32 bit .wav file.")
parser.add_argument("-m", "--measure", type=int, help="Start a measurement of a fixed length, providing the length in seconds")
parser.add_argument("-c", "--calibrate", type=int, help="Calibrate the microphone and store the calibration value for the next measurement")
args = parser.parse_args()

def main():
    start_ui = True

    # Simulation
    wav_path = None
    should_simulate = args.simulate is not None

    if should_simulate:
        wav_path = str(args.simulate)
        print(f"Simulating audio input using {wav_path}")

    # Start SPL Meter
    spl_meter = spl.SPLMeter(should_simulate=should_simulate, wav_path=wav_path)
    
    # Process arguments
    should_calibrate = args.calibrate is not None
    should_measure = args.measure is not None
    start_ui = not should_calibrate and not should_measure

    if start_ui:
        spl_meter.run()
    elif should_calibrate:
        reference_db = int(args.calibrate)
        spl_meter.calibrate(reference_db)
    elif should_measure:
        measurement_length = int(args.measure)
        spl_meter.measure(measurement_length)

if __name__ == "__main__":
    main()
