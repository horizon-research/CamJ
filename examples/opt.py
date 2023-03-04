import argparse
import sys

def options():

    parser = argparse.ArgumentParser()
    # if there is no argment in the input, print help
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    
    # validation examples
    parser.add_argument(
        "--isscc_17_0_62",
        default=False,
        action="store_true",
        help="Run ISSCC 17 0.62V example",
    )
    parser.add_argument(
        "--jssc_19",
        default=False,
        action="store_true",
        help="Run JSSC 19 example",
    )
    parser.add_argument(
        "--sensors_20",
        default=False,
        action="store_true",
        help="Run Sensors 20 example",
    )
    parser.add_argument(
        "--isscc_21",
        default=False,
        action="store_true",
        help="Run ISSCC 21 Back-illuminated example",
    )
    parser.add_argument(
        "--jssc21_05v",
        default=False,
        action="store_true",
        help="Run JSSC 21 0.5V example",
    )
    parser.add_argument(
        "--jssc21_51pj",
        default=False,
        action="store_true",
        help="Run JSSC 21 51pJ example",
    )
    parser.add_argument(
        "--vlsi_21",
        default=False,
        action="store_true",
        help="Run VLSI 21 example",
    )
    parser.add_argument(
        "--isscc_22_08v",
        default=False,
        action="store_true",
        help="Run ISSCC 22 0.8V example",
    )
    parser.add_argument(
        "--tcas_i22",
        default=False,
        action="store_true",
        help="Run TCAS-I 22 example",
    )
    
    # evaluation examples
    parser.add_argument(
        "--ieee_vr22",
        default=False,
        action="store_true",
        help="Run IEEE VR22 example",
    )

    return parser.parse_args()