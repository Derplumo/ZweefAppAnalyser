import pandas as pd
import os
from math import floor
from tabulate import tabulate


def analyse_flight_console():
    """
    files required:
    - csv file containing the log from de ZweefApp
    - callsigns.txt (with callsigns and types in the following format: "PH-1337: ASK-21")
        This is used for determining types when only the callsign is given
    """

    print("The input for this flight analyser is the csv file from the 'ZweefApp'. To get all flights from this source "
          "be sure to set the right start and end date for the filter. The ZweefApp does not seem to work well with "
          "empty dates at the moment.")
    print("")
    return analyse_core()


def find_and_read_flight_file():
    try:
        csv_file = find_csv_file()
        csv_input = input(f"Would you like to use the following file for analysis: {csv_file}? (Y/N)")
        if csv_input.upper() != "Y":
            csv_file = input(f"Provide the path of the csv file to use: ")
        flights = read_flight_log(csv_file)
        return flights
    except FileNotFoundError:
        print("The provided file could not be found. Please check the extension of the file "
              "(does it have '.csv' behind it?) and the path (should be absolute).")
        return find_and_read_flight_file()
    except:
        print("Something went wrong. Try again or contact the developer.")


def find_pilot_name(flights):
    try:
        pilot_name = get_pilot_name_from_file(flights)
        pilot_name_confirmation = input(f"Is the pilots name: {pilot_name} (Y/N)")
        if pilot_name_confirmation.upper() != "Y":
            pilot_name = input(f"Please enter the pilots name:")

        valid_flights = select_valid_flights(flights, pilot_name)
        if len(valid_flights) > 0:
            return pilot_name, valid_flights
        else:
            print("The provided name was not found in the provided csv file. Please check your input.")
            return find_pilot_name(flights)
    except:
        print("Something went wrong")
        exit()


def analyse_core():
    flights = find_and_read_flight_file()

    pilot_name, valid_flights = find_pilot_name(flights)

    exam_date = get_exam_date(valid_flights)
    date_solo = get_date_solo(valid_flights, pilot_name)
    date_last_checkstart = get_date_checkstart(valid_flights)

    total_hours = get_total_hours(valid_flights)
    total_hours_spl = get_total_hours_after_spl(valid_flights, exam_date)
    total_flights = get_total_starts(valid_flights)
    total_flights_spl = get_total_starts_after_spl(valid_flights, exam_date)

    results_types = get_type_results(valid_flights, exam_date, pilot_name)

    overlands_solo = get_overlands_solo(valid_flights, pilot_name)
    overlands_pic = get_overlands_pic(valid_flights, pilot_name)
    overlands_passenger = get_overlands_passenger(valid_flights, pilot_name)

    five_hours = get_five_hours(valid_flights, pilot_name)
    fifty_kilometer = get_fifty_kilometer(valid_flights, pilot_name)

    print("")
    print("Results")
    print("----------------------------------------")
    print_statistic('date exam', exam_date)
    print_statistic('date solo', date_solo)
    print_statistic('date last checkstart', date_last_checkstart)
    print("")
    print_statistic('total hours', total_hours)
    print_statistic('total hours after SPL', total_hours_spl)
    print_statistic('total starts/flights', total_flights)
    print_statistic('total starts/flights after SPL', total_flights_spl)
    print("")
    print(tabulate(results_types, headers="keys"))
    print("")
    print_statistic("overlands solo", overlands_solo)
    print_statistic("overlands pic", overlands_pic)
    print_statistic("overlands with passenger", overlands_passenger)
    print_statistic("date five hours", five_hours)
    print_statistic("date fifty kilometers", fifty_kilometer)

    print("")
    _ = input("please press enter to close")
    return exam_date, date_solo, date_last_checkstart, \
        total_hours, total_hours_spl, total_flights, total_flights_spl, results_types


def print_statistic(name, value):
    if value is None:
        value = "not applicable"
    if isinstance(value, pd.Timestamp):
        value = value.strftime("%Y-%m-%d")
    print("{:<30} {:<30}".format(name, value))

def find_csv_file():
    for file in os.listdir(os.getcwd()):
        if file.endswith(".csv") and "callsigns" not in file:
            return file


def read_flight_log(csv_file):
    flights = pd.read_csv(csv_file)
    flights["datum"] = pd.to_datetime(flights["datum"])
    return flights


def get_pilot_name_from_file(flights):
    gezagvoerders = flights["gezagvoerder_naam"].to_list()
    tweede_inzittende = flights["tweede_inzittende_naam"].to_list()
    vliegers_namen = []
    vliegers_namen.extend(gezagvoerders)
    vliegers_namen.extend(tweede_inzittende)
    return most_frequent(vliegers_namen)


def most_frequent(input_list):
    return max(set(input_list), key=input_list.count)


def get_exam_date(flights):
    subset = flights[flights["is_examen"]]
    if len(subset) == 0:
        return None
    idmax = subset["datum"].idxmax()
    return subset.loc[idmax].datum


def get_date_solo(flights, pilot_name):
    subset = flights[(flights["gezagvoerder_naam"] == pilot_name) & ((flights["tweede_inzittende_naam"].isna()) |
                                                                     (flights["tweede_inzittende_naam"] == pilot_name))]
    if len(subset) == 0:
        return None
    idmin = subset["datum"].idxmin()
    return subset.loc[idmin].datum


def get_date_checkstart(flights):
    subset = flights[
        (flights["is_fis"]) | (flights["is_training"]) | (flights["is_examen"]) | (flights["is_profcheck"])]
    if len(subset) == 0:
        return None
    idmax = subset["datum"].idxmax()
    return subset.loc[idmax].datum


def get_total_hours(flights):
    sum_hours = flights["vluchtduur"].sum()
    return f"{floor(sum_hours / 60)}h{sum_hours % 60}m"


def get_total_hours_after_spl(flights, exam_date):
    if exam_date is None:
        return 0

    subset = flights[flights["datum"] > exam_date]
    if len(subset) == 0:
        return 0
    return get_total_hours(subset)


def get_total_starts(flights):
    count_starts = len(flights)
    return count_starts


def get_total_starts_after_spl(flights, exam_date):
    if exam_date is None:
        return 0

    subset = flights[flights["datum"] > exam_date]
    if len(subset) == 0:
        return 0
    return get_total_starts(subset)


def get_type_results(flights, exam_date, pilot_name):
    """
    1. total type starts
    2. total type starts after spl
    3. total type starts solo
    4. total type hours
    5. total type hours after spl
    6. total type overlands
    """

    aircraft_types = select_types(flights)
    results = {}
    for aircraft_type, callsigns in aircraft_types.items():
        results[aircraft_type] = [
            get_type_starts(flights, callsigns),
            get_type_starts_spl(flights, callsigns, exam_date),
            get_type_starts_solo(flights, callsigns, pilot_name),
            get_type_hours(flights, callsigns),
            get_type_hours_spl(flights, callsigns, exam_date),
            get_type_overlands(flights, callsigns)
        ]
    rows = ["total starts on type",
            "total starts on type after SPL",
            "total solo starts on type",
            "total hours on type",
            "total hours on type after SPL",
            "total times overland on type"
            ]
    dataframe = pd.DataFrame(data=results, index=rows)
    return dataframe


def select_types(flights):
    unique_callsigns = flights["registratie"].unique()
    aircraft_types = {}
    for callsign in unique_callsigns:
        callsign_types = flights[(flights["registratie"] == callsign) & flights["type"].notna()]["type"]
        if len(callsign_types) >= 1:
            callsign_type = callsign_types.iloc[0]
        else:
            callsign_type = input(f"Please enter the aircraft type for {callsign} as it could not be found in the log.")

        callsign_type = simplify_callsign(callsign_type)

        if callsign_type not in aircraft_types.keys():
            aircraft_types[callsign_type] = [callsign]
        else:
            aircraft_types[callsign_type].append(callsign)

    return aircraft_types


def select_valid_flights(flights, pilot_name):
    return flights[(flights["gezagvoerder_naam"] == pilot_name) |
                   ((flights["tweede_inzittende_naam"] == pilot_name) &
                    ((flights["is_fis"]) | (flights["is_training"]) | (flights["is_examen"]) | (
                        flights["is_profcheck"])))]


def simplify_callsign(aircraft_type):
    if aircraft_type == "LS 4a" or aircraft_type == "LS-4":
        return "LS-4a"
    return aircraft_type


def get_type_starts(flights, callsigns):
    subset = flights[flights["registratie"].isin(callsigns)]
    return len(subset)


def get_type_starts_spl(flights, callsigns, exam_date):
    if exam_date is None:
        return 0

    subset = flights[(flights["registratie"].isin(callsigns)) & (flights["datum"] > exam_date)]
    return len(subset)


def get_type_starts_solo(flights, callsigns, pilot_name):
    subset = flights[(flights["registratie"].isin(callsigns)) & (flights["gezagvoerder_naam"] == pilot_name) & (
        (flights["tweede_inzittende_naam"].isna()) | (flights["tweede_inzittende_naam"] == pilot_name))]
    return len(subset)


def get_type_hours(flights, callsigns):
    subset = flights[flights["registratie"].isin(callsigns)]
    sum_hours = subset["vluchtduur"].sum()
    return f"{floor(sum_hours / 60)}h{sum_hours % 60}m"


def get_type_hours_spl(flights, callsigns, exam_date):
    if exam_date is None:
        return 0

    subset = flights[(flights["registratie"].isin(callsigns)) & (flights["datum"] > exam_date)]
    if len(subset) == 0:
        return "0h0m"
    sum_hours = subset["vluchtduur"].sum()
    return f"{floor(sum_hours / 60)}h{sum_hours % 60}m"


def get_type_overlands(flights, callsigns):
    subset = flights[(flights["registratie"].isin(callsigns)) & (flights["is_overland"])]
    return len(subset)


def get_overlands_solo(flights, pilot_name):
    subset = flights[(flights["is_overland"]) & (flights["gezagvoerder_naam"] == pilot_name) & (
        (flights["tweede_inzittende_naam"].isna()) | (flights["tweede_inzittende_naam"] == pilot_name))]
    return len(subset)


def get_overlands_pic(flights, pilot_name):
    subset = flights[(flights["is_overland"]) & (flights["gezagvoerder_naam"] == pilot_name)]
    return len(subset)


def get_overlands_passenger(flights, pilot_name):
    subset = flights[(flights["is_overland"]) & (flights["gezagvoerder_naam"] == pilot_name) &
                     ((flights["tweede_inzittende_naam"].notna()) & (flights["is_fis"] is False) &
                      (flights["is_training"] is False) & (flights["is_examen"] is False) &
                      (flights["is_profcheck"] is False))]
    return len(subset)


def get_five_hours(flights, pilot_name):
    subset = flights[(flights["vluchtduur"] > 5 * 60) & (flights["gezagvoerder_naam"] == pilot_name)]
    if len(subset) == 0:
        return None
    idmax = subset["datum"].idxmin()
    return subset.loc[idmax].datum.strftime("%Y-%m-%d")


def get_fifty_kilometer(flights, pilot_name):
    subset = flights[(flights["afstand"] > 50) & (flights["gezagvoerder_naam"] == pilot_name)]
    if len(subset) == 0:
        return None
    idmax = subset["datum"].idxmin()
    return subset.loc[idmax].datum.strftime("%Y-%m-%d")


if __name__ == "__main__":
    analyse_flight_console()
