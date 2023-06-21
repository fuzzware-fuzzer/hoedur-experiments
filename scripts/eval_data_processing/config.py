import os
from pathlib import Path

import yaml


def env(var, default=None):
    return os.environ.get(var) or default


def parse_duration(value):
    if 's' in value:
        return int(value.rstrip('s'))
    elif 'm' in value:
        return int(value.rstrip('m')) * 60
    elif 'h' in value:
        return int(value.rstrip('h')) * 60 * 60
    elif 'd' in value:
        return int(value.rstrip('d')) * 60 * 60 * 24
    else:
        print(f'ERROR: unknown duration format "{value}"')
        return False


DIR = Path(os.path.dirname(os.path.realpath(__file__)))
default_base_dir = str(DIR.parents[1]) if len(DIR.parents) >= 2 else "/home/user/hoedur-experiments"
BASEDIR = Path(env('BASEDIR', default_base_dir))

FUZZER_NAME = {
    'fuzzware': 'Fuzzware',
    'hoedur': 'Hoedur',
    'hoedur-dict': 'Hoedur+Dict',
    'hoedur-single-stream': 'Single-Stream-Hoedur',
    'hoedur-single-stream-dict': 'Single-Stream-Hoedur+Dict',
}
FUZZER_COLOR = {
    'fuzzware': '#109426',
    'hoedur': '#f59c0c',
    'hoedur-dict': '#d66368',
    'hoedur-single-stream': '#0f71bd',
    'hoedur-single-stream-dict': '#a307a8',
}
FUZZER_SHAPE = {
    'fuzzware': 'cross',
    'hoedur': 'square',
    'hoedur-dict': 'diamond',
    'hoedur-single-stream': 'triangle-right',
    'hoedur-single-stream-dict': 'triangle-up',
}
FUZZER_LATEX = {
    'fuzzware': '\\fuzzware',
    'hoedur': '\\hoedur',
    'hoedur-single-stream': '\\shoedur',
}

EXPERIMENTS = {
    # experiment name
    '01-bug-finding-ability': {
        'path': BASEDIR / '01-bug-finding-ability',
        'fuzzer': [
            'fuzzware',
            'hoedur-single-stream',
            'hoedur',
        ],
        # scale factor baseline
        'baseline': 'hoedur',
        # fuzzing targets
        'target': [
            'Fuzzware/contiki-ng/CVE-2020-12140',
            'Fuzzware/contiki-ng/CVE-2020-12141',
            'Fuzzware/zephyr-os/CVE-2020-10064',
            'Fuzzware/zephyr-os/CVE-2020-10065',
            'Fuzzware/zephyr-os/CVE-2020-10066',
            'Fuzzware/zephyr-os/CVE-2021-3319',
            'Fuzzware/zephyr-os/CVE-2021-3320',
            'Fuzzware/zephyr-os/CVE-2021-3321',
            'Fuzzware/zephyr-os/CVE-2021-3322',
            'Fuzzware/zephyr-os/CVE-2021-3323',
            'Fuzzware/zephyr-os/CVE-2021-3329',
            'Fuzzware/zephyr-os/CVE-2021-3330',
        ],
        # fuzzing target : list of bugs with arbitrary code execution (excluded in coverage)
        'ace_bugs': {
            'Fuzzware/contiki-ng/CVE-2020-12140': [
                'CVE-2020-12140',
                'fixed-Bug-SRH_too_many_segments_left',
                'fixed-Bug-invalid_SRH_address_pointer',
                'fixed-Bug-uncompress_hdr_iphc_oob_write',
                'fixed-Bug-6lo_firstfrag_oob_write',
            ],
            'Fuzzware/contiki-ng/CVE-2020-12141': [
                'CVE-2020-12141',
                'fixed-Bug-snmp_oid_decode_oid_oob',
                'fixed-Bug-snmp_engine_get_bulk-varbinds_length-oob',
            ],
        },
        # timing tables
        'timings': {
            # fuzzing target : list of bug hooks
            'fuzzware-cve': {
                'Fuzzware/contiki-ng/CVE-2020-12140': ['CVE-2020-12140'],
                'Fuzzware/contiki-ng/CVE-2020-12141': ['CVE-2020-12141'],
                'Fuzzware/zephyr-os/CVE-2020-10064': ['CVE-2020-10064'],
                'Fuzzware/zephyr-os/CVE-2020-10065': ['CVE-2020-10065'],
                'Fuzzware/zephyr-os/CVE-2020-10066': ['CVE-2020-10066'],
                'Fuzzware/zephyr-os/CVE-2021-3319': ['CVE-2021-3319'],
                'Fuzzware/zephyr-os/CVE-2021-3320': ['CVE-2021-3320'],
                'Fuzzware/zephyr-os/CVE-2021-3321': ['CVE-2021-3321'],
                'Fuzzware/zephyr-os/CVE-2021-3322': ['CVE-2021-3322'],
                'Fuzzware/zephyr-os/CVE-2021-3323': ['CVE-2021-3323'],
                'Fuzzware/zephyr-os/CVE-2021-3329': ['CVE-2021-3329'],
                'Fuzzware/zephyr-os/CVE-2021-3330': ['CVE-2021-3330'],
            },
            # fuzzing target : list of bug hooks
            'new-bugs': {
                'Fuzzware/zephyr-os/CVE-2021-3329': [
                    'new-Bug-invalid-init-le_read_buffer_size',
                    'new-Bug-sent_cmd_shared_ref_race',
                    'new-Bug-hci_prio_event_alloc_err_handling',
                    'new-Bug-hci-send_sync-dangling-sema-ref',
                    'new-Bug-hci-send_sync-dangling-conn-state-ref',
                ],
                'Fuzzware/contiki-ng/CVE-2020-12140': [
                    'new-Bug-unchecked_sdu_length',
                    'new-Bug-l2cap_mtu_6lo_output_packetbuf_oob_write',
                    'new-Bug-ipv6_routing_infinite_recursion',
                ]
            },
            # fuzzing target : list of bug hooks
            'fixed-bugs': {
                'Fuzzware/contiki-ng/CVE-2020-12140': [
                    'fixed-Bug-SRH_too_many_segments_left',
                    'fixed-Bug-invalid_SRH_address_pointer',
                    'fixed-Bug-uncompress_hdr_iphc_oob_write',
                    'fixed-Bug-6lo_firstfrag_oob_write',
                ],
                'Fuzzware/contiki-ng/CVE-2020-12141': [
                    'fixed-Bug-snmp_oid_decode_oid_oob',
                    'fixed-Bug-snmp_oid_copy-missing-terminator-oob',
                    'fixed-Bug-snmp_engine_get_bulk-varbinds_length-oob',
                ],
                'Fuzzware/zephyr-os/CVE-2020-10064': [
                    'fixed-Bug-fragment_header_len',
                ],
                'Fuzzware/zephyr-os/CVE-2021-3329': [
                    'fixed-Bug-k_poll-race-condition',
                    'fixed-Bug-bt_att-resp-timeout-null-ptr',
                    'fixed-Bug-bt-periph-update_conn_param-work-double-submit',
                    'fixed-Bug-double-bt_att_chan_req_send-null-ptr',
                ],
            }
        }
    },
    # experiment name
    '02-coverage-est-data-set': {
        'path': BASEDIR / '02-coverage-est-data-set',
        'fuzzer': [
            'fuzzware',
            'hoedur',
            'hoedur-single-stream',
        ],
        # fuzzing targets
        'target': [
            'HALucinator/6LoWPAN_Receiver',
            'P2IM/CNC',
            'P2IM/Console',
            'P2IM/Drone',
            'P2IM/Gateway',
            'P2IM/Heat_Press',
            'P2IM/PLC',
            'P2IM/Reflow_Oven',
            'P2IM/Robot',
            'P2IM/Soldering_Iron',
            'P2IM/Steering_Control',
            'Pretender/RF_Door_Lock',
            'Pretender/Thermostat',
            'uEmu/3Dprinter',
            'uEmu/GPSTracker',
            'uEmu/LiteOS_IoT',
            'uEmu/utasker_MODBUS',
            'uEmu/utasker_USB',
            'uEmu/Zepyhr_SocketCan',
            'WYCINWYC/XML_Parser',
        ],
        # selected targets for ablation stutdy (paper / appendix filter)
        'include_in_paper': [
            'HALucinator/6LoWPAN_Receiver',
            'P2IM/CNC',
            'P2IM/Gateway',
            'P2IM/Soldering_Iron',
            'Pretender/Thermostat',
            'uEmu/3Dprinter',
            'uEmu/Zepyhr_SocketCan',
            'WYCINWYC/XML_Parser',
        ],
    },
    # experiment name
    '03-advanced-mutations': {
        'path': BASEDIR / '03-advanced-mutations',
        'fuzzer': [
            'hoedur',
            'hoedur-dict',
            'hoedur-single-stream',
            'hoedur-single-stream-dict',
        ],
        'symlink_fuzzer': {
            'hoedur': '02-coverage-est-data-set',
            'hoedur-single-stream': '02-coverage-est-data-set',
        },
        # fuzzing targets
        'target': [
            'P2IM/Console',
            'uEmu/utasker_MODBUS',
            'uEmu/utasker_USB',
            'uEmu/Zepyhr_SocketCan',
        ],
    },
    # experiment name
    '04-prev-unknown-vulns': {
        'path': BASEDIR / '04-prev-unknown-vulns',
        'fuzzer': [
            'hoedur',
        ],
        # fuzzing targets
        'target': [
            'Hoedur/contiki-ng/CVE-2022-41873',
            'Hoedur/contiki-ng/CVE-2022-41972',
            'Hoedur/contiki-ng/CVE-2023-31129',
            'Hoedur/loramac-node/CVE-2022-39274',
            'Hoedur/riot/CVE-2023-24817',
            'Hoedur/riot/CVE-2023-24818',
            'Hoedur/riot/CVE-2023-24819',
            'Hoedur/riot/CVE-2023-24820',
            'Hoedur/riot/CVE-2023-24821',
            'Hoedur/riot/CVE-2023-24822',
            'Hoedur/riot/CVE-2023-24823',
            'Hoedur/riot/CVE-2023-24825',
            'Hoedur/riot/CVE-2023-24826',
            'Hoedur/zephyr-os/CVE-2022-3806',
        ],
    }
}

# set name for easy usage in scripts
for name, experiment in EXPERIMENTS.items():
    experiment['name'] = name


def load_file(path):
    if not os.path.isfile(path):
        print(f'ERROR: config file "{path}" missing')

    try:
        return open(path).read()
    except Exception as e:
        print(f'ERROR: could not load config file "{path}": {e}')
        exit(1)


# load eval profile
def load_run_time_profile():
    active_profile = load_file(
        BASEDIR / 'experiment-config' / 'active_profile.txt').strip()

    try:
        profiles = yaml.safe_load(
            load_file(BASEDIR / 'experiment-config' / 'profiles.yml'))

        return profiles[active_profile]
    except Exception as e:
        print(f'ERROR: failed to parse config file "profiles.yml": {e}')
        exit(1)


# apply selected profile
for (name, profile) in load_run_time_profile().items():
    EXPERIMENTS[name]['runs'] = profile['runs']

    if 'cores_per_run' in profile:
        EXPERIMENTS[name]['cores'] = profile['cores_per_run']

    # verify human readable duration format is valid
    duration = profile['duration']
    if parse_duration(duration):
        EXPERIMENTS[name]['duration'] = duration
    else:
        exit(1)

# bug description to CVE lookup table
BUG_DESCRIPTION = {
    # new Bugs (CVE)
    'new-Bug-ipv6_routing_infinite_recursion': 'CVE-2023-29001',
    'new-Bug-unchecked_sdu_length': 'CVE-2023-23609',
    'new-Bug-l2cap_mtu_6lo_output_packetbuf_oob_write': 'CVE-2023-28116',
    'new-Bug-invalid-init-le_read_buffer_size': 'CVE-2023-0397',
    'new-Bug-sent_cmd_shared_ref_race': 'CVE-2023-1422',
    'new-Bug-hci_prio_event_alloc_err_handling': 'CVE-2023-1423',
    'new-Bug-hci-send_sync-dangling-sema-ref': 'CVE-2023-1901',
    'new-Bug-hci-send_sync-dangling-conn-state-ref': 'CVE-2023-1902',

    # fixed Bugs
    'fixed-Bug-SRH_too_many_segments_left': 'FIXED-1',
    'fixed-Bug-invalid_SRH_address_pointer': 'FIXED-2',
    'fixed-Bug-uncompress_hdr_iphc_oob_write': 'FIXED-3',
    'fixed-Bug-6lo_firstfrag_oob_write': 'FIXED-4',
    'fixed-Bug-snmp_oid_decode_oid_oob': 'FIXED-5',
    'fixed-Bug-snmp_oid_copy-missing-terminator-oob': 'FIXED-6',
    'fixed-Bug-snmp_engine_get_bulk-varbinds_length-oob': 'FIXED-7',
    'fixed-Bug-fragment_header_len': 'FIXED-8',
    'fixed-Bug-k_poll-race-condition': 'FIXED-9',
    'fixed-Bug-bt_att-resp-timeout-null-ptr': 'FIXED-10',
    'fixed-Bug-bt-periph-update_conn_param-work-double-submit': 'FIXED-11',
    'fixed-Bug-double-bt_att_chan_req_send-null-ptr': 'FIXED-12',
}
