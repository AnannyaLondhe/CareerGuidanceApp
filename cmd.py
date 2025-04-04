 # Check command-line arguments
        run_entities = "--run_entities" in sys.argv
        run_individual = "--run_individual" in sys.argv

        # Step 1: Run ENTITIES, ASSOCIATION, and ENTITIES_KYC together if flag is set
        if run_entities:
            lg.step_name = "Executing ENTITIES, ASSOCIATION, and ENTITIES_KYC in one step"
            lg.start_step()

            for operator, field in operator_config_dic.items():
                if operator in ["ENTITIES", "ASSOCIATION", "ENTITIES_KYC"]:
                    print(f"Running {operator}")
                    lg.rc = endpoint_check(operator, field, process, del_crds_rec)

            lg.end_step()

        # Step 2: Run INDIVIDUAL separately if flag is set
        if run_individual:
            lg.step_name = "Executing INDIVIDUAL in a separate step"
            lg.start_step()

            for operator, field in operator_config_dic.items():
                if operator == "INDIVIDUAL":
                    print(f"Running {operator}")
                    lg.rc = endpoint_check(operator, field, process, del_crds_rec)

            lg.end_step()
