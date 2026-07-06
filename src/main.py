import SPLMeter as spl
import argparse

parser = argparse.ArgumentParser(description="An SPL Meter.")
parser.add_argument("-s", "--simulate", type=str, help="Simulate audio input using a 16/32 bit .wav file.")
parser.add_argument("-m", "--measure", type=int, help="Start a measurement of a fixed length, providing the length in seconds")
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
    
    start_ui = args.measure is None
    if start_ui:
        spl_meter.run()
    else:
        # Fixed measurement without UI
        measurement_length = int(args.measure)
        spl_meter.measure(measurement_length)

if __name__ == "__main__":
    main()
