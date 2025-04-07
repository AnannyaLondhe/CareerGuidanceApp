import oracledb
import sys
import traceback
import os
from datetime import datetime

sys.path.insert(8, '/apps/infocaml/AMLTEN/scripts/python')

from icdb import ICDatabase, ICDatabaseError
from lib_functions import logger  # User-defined
from send_mail import send_mail

# Initialize logger
lg = logger()
lg.tenant = "AMLTEN"
lg.script_name = os.path.basename(__file__)
lg.script_path = os.environ.get("AML_TEN_PYTHON")
lg.oracle_sid = ""

lg.job = "amlten_check_data_validation.py"
lg.start_script()

# Set database schema and input arguments
my_schema = "JOBRUN"
inputarg = str(sys.argv[1:])[1:-1]
autosys_job = inputarg.strip("")
autosys_schema = autosys_job.split('_')[0]

# Initialize DB connection
mydb = ICDatabase(my_schema)
conn = mydb.getDbConn(my_schema)
cur = conn.cursor()

curr_time = datetime.now().strftime('%Y%m%d%H%M%S')
dest_dir = os.environ.get('CDROUT') + "/aml/"
Exception_dir = r"/data/infocaml/cft_data/send/"

ultimate_status = 'FAIL'


def is_weekend(date_string):
    try:
        dt_obj = datetime.strptime(date_string, '%d-%b-%Y')
        return dt_obj.weekday() >= 5  # 5 = Saturday, 6 = Sunday
    except Exception as e:
        lg.dfnLogSTDout(f"Error parsing date {date_string}: {str(e)}")
        return False


def fn_get_as_of_dt(v_db_schema, v_date_id):
    try:
        if v_db_schema == 'EASTNET':
            sql_as_of_dt = "SELECT NVL(CURR_AS_OF_DT, PREV_AS_OF_DT) FROM amlten.t_file_process_batch WHERE TENANT_CD = 20"
        elif v_db_schema == 'AML':
            sql_as_of_dt = f"SELECT date_value FROM aml.t_aml_application_date WHERE date_id = '{v_date_id}'"
        elif v_db_schema == 'AMLTEN':
            sql_as_of_dt = f"SELECT date_value FROM amlca.t_aml_application_date WHERE date_id = '{v_date_id}'"
        elif v_db_schema in ['AML_ACTMZE_STG_US', 'AML_ACTMZE_STG_CA']:
            sql_as_of_dt = f"SELECT CURR_AS_OF_DT FROM aml.t_act_etl1_batch WHERE CURR_STATUS = 'SUCCESS'"
        else:
            lg.dfnLogSTDout("ERROR: Pass a valid autosys job name starting with EASTNET, AML, or AMLCA")
            raise ValueError("Invalid schema")

        cur.execute(sql_as_of_dt)
        v_as_of_dt = cur.fetchone()[0].strftime('%d-%b-%Y')
        return v_as_of_dt

    except Exception as err:
        lg.dfnLogSTDout(f"Unexpected {err}, {type(err)}")
        raise


def FN_AML_CHECK_DATA_VALIDATION():
    try:
        sql_main = f"""
            SELECT * FROM AMLTEN.T_AML_DATA_VALIDATION_CONFIG 
            WHERE AUTOSYS_JOB_NM = '{autosys_job}' AND is_active = 1
        """
        cur.execute(sql_main)
        sql_main_data = cur.fetchall()

        lg.dfnLogSTDout(f'Running for {autosys_schema}')
        error_ID_List = []

        for row in sql_main_data:
            v_as_of_dt = fn_get_as_of_dt(autosys_schema, row[2])
            
            # 🚫 Skip weekends
            if is_weekend(v_as_of_dt):
                lg.dfnLogSTDout(f"Skipping validation for weekend date: {v_as_of_dt}")
                
                # Optional: send info email if you want visibility (disabled by default)
                # subject = f"Skipped: Validation for {autosys_job} on {v_as_of_dt} (Weekend)"
                # body = f"<p>Data validation was skipped for {autosys_job} as of {v_as_of_dt} because it falls on a weekend.</p>"
                # send_mail("JOBS_VALIDATION", "AMLTEN", subject, body, [])

                continue

            v_val_id = row[1]
            v_handling_type = row[5]

            lg.dfnLogSTDout(f'AS_OF_DT for {row[4]} = {v_as_of_dt}')
            v_expected_result_value = f"{row[12]} {row[13]}"

            if row[3] == 'DEVIATION_CHECK':
                sql_table_count = f"SELECT COUNT(*) FROM {row[7]}"
                cur.execute(sql_table_count)
                sql_actual_count = cur.fetchone()[0]

                sql_arch_count = f"""
                    SELECT ROUND(COUNT(*)/10) FROM {row[8]} 
                    WHERE TO_DATE(as_of_dt, 'YYYYMMDD') > TO_DATE('{v_as_of_dt}', 'DD-MON-YYYY') - 15
                    AND TO_DATE(as_of_dt, 'YYYYMMDD') <> TO_DATE('{v_as_of_dt}', 'DD-MON-YYYY')
                """
                cur.execute(sql_arch_count)
                sql_dev = cur.fetchone()[0]

                v_low_dev = sql_actual_count - round(sql_dev / row[10])
                v_high_dev = sql_actual_count + round(sql_dev / row[11])

                v_pass_fail = 'P' if v_low_dev <= sql_actual_count <= v_high_dev else 'F'

                if v_pass_fail == 'F':
                    error_ID_List.append(v_val_id)

            elif row[3] == 'VALUE_CHECK':
                cur.execute(row[9], [v_as_of_dt] if ':v_value_date' in row[9] else [])
                v_actual_result_value = cur.fetchone()[0]

                condition = f"{str(v_actual_result_value)} {row[12]} {row[13]}"
                lg.dfnLogSTDout(f"Running condition: {condition}")

                v_pass_fail = 'P' if eval(condition) else 'F'

                if v_handling_type == 'HARD' and v_pass_fail == 'F':
                    error_ID_List.append(v_val_id)

            sql_delete = f"""
                DELETE FROM AMLTEN.T_AML_DATA_VALIDATION_DTLS
                WHERE AS_OF_DT = '{v_as_of_dt}' AND AUTOSYS_JOB_NM = '{autosys_job}' AND RULE_ID = '{v_val_id}'
            """
            cur.execute(sql_delete)

            sql_insert = f"""
                INSERT INTO AMLTEN.T_AML_DATA_VALIDATION_DTLS (
                    AS_OF_DT, AUTOSYS_JOB_NM, RULE_ID, RULE_NM, ACTUAL_COUNT,
                    HIGHER_DEVIATION_COUNT, LOWER_DEVIATION_COUNT, ACTUAL_RESULT_VALUE, 
                    EXPECTED_RESULT_VALUE, PASS_FAIL, ALERT_TYPE, CRE_DT, UPD_DT, UPD_BY
                ) VALUES (
                    '{v_as_of_dt}', '{autosys_job}', '{v_val_id}', '{row[3]}', {sql_actual_count}, 
                    {v_high_dev}, {v_low_dev}, '{v_actual_result_value}', 
                    '{v_expected_result_value}', '{v_pass_fail}', '{v_handling_type}', 
                    '{v_as_of_dt}', '{v_as_of_dt}', 'F06575'
                )
            """
            cur.execute(sql_insert)

        if len(error_ID_List) >= 1:
            status = send_email(v_as_of_dt)
            if status != 0:
                lg.dfnLogSTDout("ERROR: Mail sending failed!")
                return 1

        return 0

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return 1


def send_email(v_as_of_dt):
    try:
        Exception_filename = f"{autosys_job}_REPORT_{v_as_of_dt}.csv"

        mail_sql = f"""
            SELECT AS_OF_DT, AUTOSYS_JOB_NM, RULE_ID, RULE_NM, ACTUAL_COUNT, 
                   HIGHER_DEVIATION_COUNT, LOWER_DEVIATION_COUNT, ACTUAL_RESULT_VALUE, 
                   EXPECTED_RESULT_VALUE, PASS_FAIL, ALERT_TYPE 
            FROM AMLTEN.T_AML_DATA_VALIDATION_DTLS
            WHERE AUTOSYS_JOB_NM = '{autosys_job}' AND AS_OF_DT = '{v_as_of_dt}'
            ORDER BY AS_OF_DT, AUTOSYS_JOB_NM, RULE_ID
        """
        mydb.run_sql_csv(sql=mail_sql, csvfile=Exception_dir + Exception_filename, header=True, separator=',')

        mail_subject = f'Validation failed | {autosys_job} | {v_as_of_dt}'
        html_content = f"<p>Validation failed for {autosys_job} as of {v_as_of_dt}. Check attachment.</p>"

        result_val = send_mail('JOBS_VALIDATION', 'AMLTEN', mail_subject, html_content, [Exception_dir + Exception_filename])
        return 0 if result_val == 0 else 1

    except Exception as e:
        lg.dfnLogSTDout(str(e))
        return 1


if __name__ == '__main__':
    lg.start_step()
    lg.rc = FN_AML_CHECK_DATA_VALIDATION()
    lg.end_step()
    lg.end_script()

