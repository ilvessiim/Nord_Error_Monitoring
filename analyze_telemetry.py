import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    csv_path = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_combined.csv'
    
    # Summary CSV Outputs
    output_csv_summary = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary.csv'
    output_csv_stats = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_stats.csv'
    output_csv_reasons = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_reasons.csv'
    
    # Separate CSV files for each specific problem category
    output_csv_soc_korge = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_soc_liiga_korge.csv'
    output_csv_soc_madal = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_soc_liiga_madal.csv'
    output_csv_vorgupiirang = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_vorgupiirang.csv'
    output_csv_osaline_taitmine = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_osaline_taitmine.csv'
    output_csv_ootamatu_reageering = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_ootamatu_reageering.csv'
    output_csv_uurimist_vajav = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_uurimist_vajav.csv'

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
    
    # Priority 5: Võrgupiirang (Expected grid power exceeds 50 kW grid connection capacity)
    expected_grid = df['Grid Power'] + df['ESS Power'] - df['ESS Plan']
    mask_grid = (expected_grid.abs() >= 50) | (df['Grid Power'].abs() >= 50)
    df.loc[mask_grid, 'Põhjus'] = "Võrgupiirang"
    
    # Priority 4: SOC liiga kõrge (SOC >= 90%)
    mask_soc_high = df['ESS SoC'] >= 90
    df.loc[mask_soc_high, 'Põhjus'] = "SOC liiga kõrge"
    
    # Priority 3: SOC liiga madal (SOC <= 10%)
    mask_soc_low = df['ESS SoC'] <= 10
    df.loc[mask_soc_low, 'Põhjus'] = "SOC liiga madal"
    
    # Priority 2: No Command (ESS Plan = 0)
    mask_no_cmd = (df['ESS Plan'] == 0) & (df['ESS Power'] == 0)
    df.loc[mask_no_cmd, 'Põhjus'] = "Käsku ei antud"
    
    mask_unexpected = (df['ESS Plan'] == 0) & (df['ESS Power'] != 0)
    df.loc[mask_unexpected, 'Põhjus'] = "Ootamatu reageering"
    
    # Priority 1: Käsk täidetud (Execution % >= 95%)
    mask_ok = df['Täitmise %'] >= 95
    df.loc[mask_ok, 'Põhjus'] = "Käsk täidetud"

    # Save datetime column for plotting later before cleanup
    time_dt_series = df['Time_dt']
    df = df.drop(columns=['Time_dt'])
    
    # Reorder columns
    cols = ['Time', 'ESS SoC', 'ESS Plan', 'PV Power', 'ESS Power', 'Grid Power', 'Täitmise %', 'Põhjus', 'Tund']
    df = df[cols]

    # --- Write Separate CSV Files (using detailed classifications) ---
    print("Writing separate CSV files for each category...")
    
    df[df['Põhjus'] == 'SOC liiga kõrge'].sort_values('Time').to_csv(output_csv_soc_korge, index=False)
    df[df['Põhjus'] == 'SOC liiga madal'].sort_values('Time').to_csv(output_csv_soc_madal, index=False)
    df[df['Põhjus'] == 'Võrgupiirang'].sort_values('Time').to_csv(output_csv_vorgupiirang, index=False)
    df[df['Põhjus'] == 'Osaline täitmine'].sort_values('Time').to_csv(output_csv_osaline_taitmine, index=False)
    df[df['Põhjus'] == 'Ootamatu reageering'].sort_values('Time').to_csv(output_csv_ootamatu_reageering, index=False)
    df[df['Põhjus'] == 'Viga - uurimist vajav'].sort_values('Time').to_csv(output_csv_uurimist_vajav, index=False)

    # --- Map Non-Critical Categories for summaries and charts ---
    print("Merging non-critical classifications (Osaline täitmine -> Käsk täidetud, Ootamatu reageering -> Käsku ei antud)...")
    df['Põhjus'] = df['Põhjus'].replace({
        'Osaline täitmine': 'Käsk täidetud',
        'Ootamatu reageering': 'Käsku ei antud'
    })

    # --- Generate Summary Statistics (only 4 core errors) ---
    print("Generating Summary Statistics...")
    total_rows = len(df)

    # Only the 4 core error categories
    error_categories = [
        'SOC liiga kõrge',
        'SOC liiga madal',
        'Võrgupiirang',
        'Viga - uurimist vajav'
    ]
    error_counts = df['Põhjus'].value_counts().reindex(error_categories, fill_value=0)
    total_errors = error_counts.sum()

    # Percentages calculated from total error count only
    error_pct = (error_counts / total_errors) * 100

    summary_df = pd.DataFrame({
        'Kogus (Ridade arv)': error_counts,
        'Osakaal vigadest (%)': error_pct
    })
    summary_df.index.name = 'Probleem'

    stats_df = pd.DataFrame({
        'Näitaja': [
            'Ridade koguarv',
            'Vigade koguarv (4 probleemi)',
            'SOC liiga kõrge',
            'SOC liiga madal',
            'Võrgupiirang',
            'Viga - uurimist vajav',
        ],
        'Väärtus': [
            total_rows,
            int(total_errors),
            int(error_counts['SOC liiga kõrge']),
            int(error_counts['SOC liiga madal']),
            int(error_counts['Võrgupiirang']),
            int(error_counts['Viga - uurimist vajav']),
        ]
    })

    # --- Hourly Analysis (only 4 core errors) ---
    print("Generating Hourly Analysis...")
    hourly_groups = df.groupby('Tund')

    hourly_df = pd.DataFrame(index=range(24))
    hourly_df.index.name = 'Tund'

    hourly_df['SOC liiga kõrge'] = hourly_groups['Põhjus'].apply(
        lambda s: (s == 'SOC liiga kõrge').sum()
    )
    hourly_df['SOC liiga madal'] = hourly_groups['Põhjus'].apply(
        lambda s: (s == 'SOC liiga madal').sum()
    )
    hourly_df['Võrgupiirang'] = hourly_groups['Põhjus'].apply(
        lambda s: (s == 'Võrgupiirang').sum()
    )
    hourly_df['Viga - uurimist vajav'] = hourly_groups['Põhjus'].apply(
        lambda s: (s == 'Viga - uurimist vajav').sum()
    )
    hourly_df['Vigade koguarv tunnis'] = (
        hourly_df['SOC liiga kõrge'] + hourly_df['SOC liiga madal'] +
        hourly_df['Võrgupiirang'] + hourly_df['Viga - uurimist vajav']
    )

    # --- Write Outputs to Downloads ---
    print(f"Writing combined summary to CSV: {output_csv_summary}...")
    with open(output_csv_summary, 'w', encoding='utf-8') as f:
        f.write("ÜLDINE STATISTIKA\n")
        stats_df.to_csv(f, index=False)
        f.write("\nPROBLEEMIDE JAOTUS (ainult 4 viga)\n")
        summary_df.to_csv(f, index=True)
        f.write("\nTUNNIPÕHINE ANALÜÜS (ainult 4 viga)\n")
        hourly_df.reset_index().to_csv(f, index=False)

    print(f"Writing stats to CSV: {output_csv_stats}...")
    stats_df.to_csv(output_csv_stats, index=False)

    print(f"Writing reasons to CSV: {output_csv_reasons}...")
    summary_df.to_csv(output_csv_reasons, index=True)

    # --- Clean up obsolete files ---
    obsolete_files = [
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_analyzed.xlsx',
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_analyzed.csv',
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_all_errors.csv',
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_hourly.csv',
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_errors.csv',
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_soc_high.csv',
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_soc_low.csv',
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_grid_limits.csv',
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_partial.csv',
        '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_unexpected.csv'
    ]
    for obs_file in obsolete_files:
        if os.path.exists(obs_file):
            try:
                os.remove(obs_file)
                print(f"Removed obsolete file: {obs_file}")
            except Exception as e:
                print(f"Failed to remove {obs_file}: {e}")

    # --- Generate Visualizations ---
    print("Generating visualizations...")
    charts_dir = '/Users/user/.gemini/antigravity-ide/scratch'
    os.makedirs(charts_dir, exist_ok=True)
    
    # 1. Pie Chart - only 4 core errors, percentages from error total
    plt.figure(figsize=(10, 8))
    colors_pie = ['#e74c3c', '#e67e22', '#f1c40f', '#9b59b6']
    error_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=colors_pie)
    plt.title('Probleemide jaotus (aprill 2026)', fontsize=14, fontweight='bold')
    plt.ylabel('')
    plt.tight_layout()
    pie_path = os.path.join(charts_dir, 'reason_distribution.png')
    plt.savefig(pie_path, dpi=150)
    plt.close()

    # 2. Bar Chart - only 4 core errors by hour
    plt.figure(figsize=(12, 6))
    hourly_problems = hourly_df[['SOC liiga kõrge', 'SOC liiga madal', 'Võrgupiirang', 'Viga - uurimist vajav']]
    hourly_problems.plot(
        kind='bar',
        stacked=True,
        color=['#e74c3c', '#e67e22', '#f1c40f', '#9b59b6'],
        ax=plt.gca()
    )
    plt.title('Probleemide esinemine tundide lõikes (aprill 2026)', fontsize=14, fontweight='bold')
    plt.xlabel('Tund (0-23)', fontsize=12)
    plt.ylabel('Probleemide arv', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Probleemi tüüp')
    plt.tight_layout()
    bar_path = os.path.join(charts_dir, 'problems_by_hour.png')
    plt.savefig(bar_path, dpi=150)
    plt.close()

    # 3. Timeline Chart
    df['Time_dt'] = time_dt_series
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
    print("\nProbleemide jaotus (4 viga, % vigade koguhulgast):")
    print(summary_df)

if __name__ == '__main__':
    main()
