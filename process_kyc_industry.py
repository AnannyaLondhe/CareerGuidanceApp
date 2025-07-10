def process_kyc_industry(df):
    try:
        # Ensure required identifiers exist
        required_cols = ['crdsCode', 'kycId', 'ptyId']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        # Check if KYC Industry data exists
        if 'kycData.kycIndustry' in df.columns:
            # Explode the list into rows
            df = df.explode('kycData.kycIndustry').reset_index(drop=True)

            # Normalize each dictionary in the list to columns
            kyc_industry_df = pd.json_normalize(df['kycData.kycIndustry'])

            # Rename for consistency with field mapping
            kyc_industry_df.rename(columns={
                'KycSection': 'kycSection',
                'KycActivityPercentage': 'kycActivityPercentage'
            }, inplace=True)

            # Prefix to match schema (if needed)
            kyc_industry_df.columns = [f'kycData.{col}' for col in kyc_industry_df.columns]

            # Join the identifier columns + extracted KYC industry info
            df = pd.concat([df.drop(columns=['kycData.kycIndustry']), kyc_industry_df], axis=1)

        return df

    except Exception as e:
        print("Error in process_kyc_industry:", e)
        return df
