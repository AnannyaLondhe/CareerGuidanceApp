def transform_kycindustry_data(df, process, operator, data_map_list):
   
    import pandas as pd

    # Step 1: Build field mapping from FIELD_MAP
    field_map = {}
    for row in data_map_list:
        df_col = row[2]  # OPERATOR_FIELD_NAME
        db_col = row[4]  # TAB_FIELD_NAME
        data_type = row[5]
        if df_col and db_col:
            field_map[df_col] = db_col

    # Step 2: Extract identifier fields (typically in 'identifiers')
    if 'identifiers' in df.columns:
        identifiers_expanded = pd.json_normalize(df['identifiers'])
        df = pd.concat([df.drop('identifiers', axis=1), identifiers_expanded], axis=1)

    # Step 3: Explode 'kycData.kycIndustry' field
    industry_field = 'kycData.kycIndustry'
    if industry_field not in df.columns:
        print(f"'{industry_field}' not found in dataframe.")
        return pd.DataFrame()

    df_exploded = df.explode(industry_field).reset_index(drop=True)

    # Step 4: Flatten each item in the exploded industry list
    industry_df = pd.json_normalize(df_exploded[industry_field])
    df_exploded = pd.concat([df_exploded.drop(columns=[industry_field]), industry_df], axis=1)

    # Step 5: Rename columns based on FIELD_MAP
    df_exploded = df_exploded.rename(columns=field_map)

    # Step 6: Select only required columns for DB insertion
    final_cols = list(field_map.values())
    df_final = df_exploded.loc[:, [col for col in final_cols if col in df_exploded.columns]].copy()

    return df_final
