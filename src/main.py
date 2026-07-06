import SPLMeter as spl
import argparse

parser = argparse.ArgumentParser(description="An SPL Meter.")
parser.add_argument("-s", "--simulate", type=str, help="Simulate audio input using a 16/32 bit .wav file.")
args = parser.parse_args()

def main():
    wav_path = None
    should_simulate = args.simulate is not None

    if should_simulate:
        wav_path = str(args.simulate)
        print(f"Simulating audio input using {wav_path}")

    splMeter = spl.SPLMeter(should_simulate=should_simulate, wav_path=wav_path)
    splMeter.run()

if __name__ == "__main__":
    main()
