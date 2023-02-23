import argparse
import sys

def options():

    parser = argparse.ArgumentParser()
    # if there is no argment in the input, print help
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    parser.add_argument(
        "--ieee_vr22",
        default=False,
        action="store_true",
        help="Run IEEE VR22 example",
    )
    parser.add_argument(
        "--isscc_22_08v",
        default=False,
        action="store_true",
        help="Run ISSCC 22 0.8V example",
    )
    parser.add_argument(
        "--jssc21_05v",
        default=False,
        action="store_true",
        help="Run JSSC 21 0.5V example",
    )
    parser.add_argument(
        "--tcas_i22",
        default=False,
        action="store_true",
        help="Run TCAS-I 22 example",
    )

    return parser.parse_args()