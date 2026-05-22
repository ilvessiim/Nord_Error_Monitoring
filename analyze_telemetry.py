import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    csv_path = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_combined.csv'
    output_excel = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_analyzed.xlsx'
    
    # CSV Outputs
    output_csv_detail = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_analyzed.csv'
    output_csv_summary = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary.csv'
    output_csv_errors = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_errors.csv'
    output_csv_all_errors = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_all_errors.csv'
    output_csv_soc_high = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_soc_high.csv'
    output_csv_soc_low = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_soc_low.csv'
    output_csv_grid_limit = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_grid_limits.csv'
    
    print("Loading data...")
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist.")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows.")

    # 1. Parse timestamps and extract Hour
    print("Parsing timestamps...")
    df['Time_dt'] = pd.to_datetime(df['Time'])
    df['Tund'] = df['Time_dt'].dt.hour
    
    # 2. Vectorized calculation of Täitmise %
    print("Calculating Täitmise %...")
    df['Täitmise %'] = np.nan
    
    plan_not_zero = df['ESS Plan'] != 0
    df.loc[plan_not_zero, 'Täitmise %'] = (df.loc[plan_not_zero, 'ESS Power'] / df.loc[plan_not_zero, 'ESS Plan']).abs() * 100

    # 3. Vectorized categorization of Põhjus (Reason)
    print("Categorizing reasons (Põhjus)...")
    df['Põhjus'] = "Viga - uurimist vajav"  # Default
    
    # Priority 6: Osaline täitmine (50% <= Execution % < 95%)
    mask_partial = (df['Täitmise %'] >= 50) & (df['Täitmise %'] < 95)
    df.loc[mask_partial, 'Põhjus'] = "Osaline täitmine"
    
    # Priority 5: Võrgupiirang (|Grid Power| >= 47.5 kW)
    mask_grid = df['Grid Power'].abs() >= 47.5
    df.loc[mask_grid, 'Põhjus'] = "Võrgupiirang"
    
    # Priority 4: SOC liiga kõrge laadimiseks (SOC >= 90% AND ESS Plan < 0)
    mask_soc_high = (df['ESS SoC'] >= 90) & (df['ESS Plan'] < 0)
    df.loc[mask_soc_high, 'Põhjus'] = "SOC liiga kõrge laadimiseks"
    
    # Priority 3: SOC liiga madal tühjendamiseks (SOC <= 10% AND ESS Plan > 0)
    mask_soc_low = (df['ESS SoC'] <= 10) & (df['ESS Plan'] > 0)
    df.loc[mask_soc_low, 'Põhjus'] = "SOC liiga madal tühjendamiseks"
    
    # Priority 2: No Command (ESS Plan = 0)
    mask_no_cmd = (df['ESS Plan'] == 0) & (df['ESS Power'] == 0)
    df.loc[mask_no_cmd, 'Põhjus'] = "Käsku ei antud"
    
    mask_unexpected = (df['ESS Plan'] == 0) & (df['ESS Power'] != 0)
    df.loc[mask_unexpected, 'Põhjus'] = "Ootamatu reageering"
    
    # Priority 1: Käsk täidetud (Execution % >= 95%)
    mask_ok = df['Täitmise %'] >= 95
    df.loc[mask_ok, 'Põhjus'] = "Käsk täidetud"

    # Clean up temporary datetime column
    df = df.drop(columns=['Time_dt'])
    
    # Reorder columns
    cols = ['Time', 'ESS SoC', 'ESS Plan', 'PV Power', 'ESS Power', 'Grid Power', 'Täitmise %', 'Põhjus', 'Tund']
    df = df[cols]

    # 4. Generate Summary Statistics
    print("Generating Summary Statistics...")
    total_rows = len(df)
    reason_counts = df['Põhjus'].value_counts()
    reason_pct = (reason_counts / total_rows) * 100
    
    summary_df = pd.DataFrame({
        'Kogus (Ridade arv)': reason_counts,
        'Osakaal (%)': reason_pct
    })
    summary_df.index.name = 'Põhjus'
    
    avg_execution_overall = df['Täitmise %'].mean()
    avg_execution_when_command = df.loc[df['ESS Plan'] != 0, 'Täitmise %'].mean()
    
    stats_df = pd.DataFrame({
        'Näitaja': [
            'Ridade koguarv', 
            'Keskmine täitmise % (kõik read)', 
            'Keskmine täitmise % (kui anti käsk)'
        ],
        'Väärtus': [
            total_rows, 
            avg_execution_overall, 
            avg_execution_when_command
        ]
    })

    # 5. Hourly Analysis
    print("Generating Hourly Analysis...")
    hourly_groups = df.groupby('Tund')
    
    hourly_df = pd.DataFrame(index=range(24))
    hourly_df.index.name = 'Tund'
    
    # Fix pandas future deprecation warnings by selecting specific column
    hourly_df['Käskude arv'] = hourly_groups['ESS Plan'].apply(lambda s: (s != 0).sum())
    hourly_df['Keskmine täitmise %'] = hourly_groups['Täitmise %'].mean()
    
    hourly_df['SOC probleemid'] = hourly_groups['Põhjus'].apply(
        lambda s: s.str.startswith('SOC liiga').sum()
    )
    hourly_df['Võrgupiirangud'] = hourly_groups['Põhjus'].apply(
        lambda s: (s == 'Võrgupiirang').sum()
    )
    hourly_df['Vead'] = hourly_groups['Põhjus'].apply(
        lambda s: (s == 'Viga - uurimist vajav').sum()
    )

    # 6. Filter and Export Errors
    print("Filtering errors...")
    errors_df = df[df['Põhjus'] == 'Viga - uurimist vajav'].sort_values('Time')
    print(f"Found {len(errors_df)} error rows.")
    
    # Filter all requested error types
    all_errors_list = [
        "SOC liiga kõrge laadimiseks",
        "SOC liiga madal tühjendamiseks",
        "Võrgupiirang",
        "Viga - uurimist vajav"
    ]
    all_errors_df = df[df['Põhjus'].isin(all_errors_list)].sort_values('Time')
    print(f"Found {len(all_errors_df)} total rows matching requested error categories.")

    # 7. Write to Excel using openpyxl
    print(f"Writing to Excel file: {output_excel}...")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Õige SOC', index=False)
        stats_df.to_excel(writer, sheet_name='Kokkuvõte', startrow=0, index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Kokkuvõte']
        worksheet.cell(row=6, column=1, value="Põhjuste jaotus:")
        summary_df.to_excel(writer, sheet_name='Kokkuvõte', startrow=6, index=True)
        
        worksheet.cell(row=18, column=1, value="Tunnipõhine analüüs:")
        hourly_df.reset_index().to_excel(writer, sheet_name='Kokkuvõte', startrow=18, index=False)
        errors_df.to_excel(writer, sheet_name='Vead', index=False)
        
    # 8. Write to CSV files for easy local viewing on Macbook
    print(f"Writing detailed output to CSV: {output_csv_detail}...")
    df.to_csv(output_csv_detail, index=False)
    
    print(f"Writing unexplained errors output to CSV: {output_csv_errors}...")
    errors_df.to_csv(output_csv_errors, index=False)
    
    print(f"Writing SOC too high errors to CSV: {output_csv_soc_high}...")
    df[df['Põhjus'] == 'SOC liiga kõrge laadimiseks'].sort_values('Time').to_csv(output_csv_soc_high, index=False)
    
    print(f"Writing SOC too low errors to CSV: {output_csv_soc_low}...")
    df[df['Põhjus'] == 'SOC liiga madal tühjendamiseks'].sort_values('Time').to_csv(output_csv_soc_low, index=False)
    
    print(f"Writing Grid Limit constraint errors to CSV: {output_csv_grid_limit}...")
    df[df['Põhjus'] == 'Võrgupiirang'].sort_values('Time').to_csv(output_csv_grid_limit, index=False)
    
    print(f"Writing all requested errors combined to CSV: {output_csv_all_errors}...")
    all_errors_df.to_csv(output_csv_all_errors, index=False)
    
    print(f"Writing combined summary to CSV: {output_csv_summary}...")
    with open(output_csv_summary, 'w', encoding='utf-8') as f:
        f.write("KOKKUVÕTE NÄITAJAD\n")
        stats_df.to_csv(f, index=False)
        f.write("\nPÕHJUSTE JAOTUS\n")
        summary_df.to_csv(f, index=True)
        f.write("\nTUNNIPÕHINE ANALÜÜS\n")
        hourly_df.reset_index().to_csv(f, index=False)
        
    # Also write separate clean CSVs for easy importing into Numbers/Excel on MacBook
    stats_df.to_csv('/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_stats.csv', index=False)
    summary_df.to_csv('/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_reasons.csv', index=True)
    hourly_df.reset_index().to_csv('/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_hourly.csv', index=False)

    print("Excel and CSV files created successfully.")

    # 9. Visualizations
    print("Generating visualizations...")
    charts_dir = '/Users/user/.gemini/antigravity-ide/scratch'
    os.makedirs(charts_dir, exist_ok=True)
    
    # Pie Chart
    plt.figure(figsize=(10, 8))
    reason_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired(np.linspace(0, 1, len(reason_counts))))
    plt.title('Põhjuste jaotus (aprill 2026)', fontsize=14, fontweight='bold')
    plt.ylabel('')
    plt.tight_layout()
    pie_path = os.path.join(charts_dir, 'reason_distribution.png')
    plt.savefig(pie_path, dpi=150)
    plt.close()
    
    # Bar Chart
    plt.figure(figsize=(12, 6))
    hourly_problems = hourly_df[['SOC probleemid', 'Võrgupiirangud', 'Vead']]
    hourly_problems.plot(kind='bar', stacked=True, color=['#e74c3c', '#f39c12', '#9b59b6'], ax=plt.gca())
    plt.title('Probleemide esinemine tundide lõikes', fontsize=14, fontweight='bold')
    plt.xlabel('Tund (0-23)', fontsize=12)
    plt.ylabel('Ridade arv', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    bar_path = os.path.join(charts_dir, 'problems_by_hour.png')
    plt.savefig(bar_path, dpi=150)
    plt.close()

    # Timeline Chart
    df['Time_dt'] = pd.to_datetime(df['Time'])
    hourly_ts = df.set_index('Time_dt').resample('h')['Täitmise %'].mean()
    
    plt.figure(figsize=(14, 6))
    plt.plot(hourly_ts.index, hourly_ts.values, label='Keskmine täitmise % (tunnipõhine)', color='#1abc9c', linewidth=1.5)
    plt.axhline(95, color='#2ecc71', linestyle='--', label='Sihtväärtus (95%)', alpha=0.8)
    plt.title('Keskmine täitmise protsent ajateljel (tunnipõhine keskmine)', fontsize=14, fontweight='bold')
    plt.xlabel('Kuupäev', fontsize=12)
    plt.ylabel('Täitmise %', fontsize=12)
    plt.legend(loc='lower left')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    timeline_path = os.path.join(charts_dir, 'execution_timeline.png')
    plt.savefig(timeline_path, dpi=150)
    plt.close()
    
    print("\n--- ANALYSIS COMPLETED ---")
    print(stats_df.to_string(index=False))
    print("\nPõhjuste jaotus:")
    print(summary_df)

if __name__ == '__main__':
    main()
