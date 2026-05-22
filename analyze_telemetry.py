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
    output_csv_daily = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_errors_by_date.csv'
    output_csv_yldine_tervis = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_yldine_tervis.csv'

    # Chart PNG outputs (saved to Downloads)
    output_png_pie = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_chart_probleemide_jaotus.png'
    output_png_hourly = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_chart_probleemid_tundide_kaupa.png'
    output_png_timeline = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_chart_taitmine_ajateljel.png'
    output_png_daily_timeline = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_chart_probleemid_paevade_kaupa.png'
    output_png_daily_pie = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_chart_probleemide_osakaalud.png'
    output_png_yldine_pie = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_chart_uldine_tervis_pie.png'
    output_png_yldine_hourly = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_chart_uldine_tervis_tundide_kaupa.png'

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

    total_normal = total_rows - total_errors
    stats_df = pd.DataFrame({
        'Näitaja': [
            'Ridade koguarv',
            'Toimib nagu peab (Normaalne töö)',
            'Vigade koguarv (4 probleemi)',
            'SOC liiga kõrge',
            'SOC liiga madal',
            'Võrgupiirang',
            'Viga - uurimist vajav',
            'Normaalne töö (%)',
            'Vigade osakaal koguajast (%)',
        ],
        'Väärtus': [
            total_rows,
            int(total_normal),
            int(total_errors),
            int(error_counts['SOC liiga kõrge']),
            int(error_counts['SOC liiga madal']),
            int(error_counts['Võrgupiirang']),
            int(error_counts['Viga - uurimist vajav']),
            round((total_normal / total_rows) * 100, 2),
            round((total_errors / total_rows) * 100, 2),
        ]
    })

    # --- Generate Overall Health Distribution (all rows) ---
    print("Generating Overall Health Distribution...")
    df['Üldine olek'] = df['Põhjus'].apply(lambda x: 'Normaalne töö' if x in ['Käsk täidetud', 'Käsku ei antud'] else x)
    overall_categories = [
        'Normaalne töö',
        'Võrgupiirang',
        'SOC liiga kõrge',
        'SOC liiga madal',
        'Viga - uurimist vajav'
    ]
    overall_counts = df['Üldine olek'].value_counts().reindex(overall_categories, fill_value=0)
    overall_pct = (overall_counts / total_rows) * 100

    overall_df = pd.DataFrame({
        'Kogus (Ridade arv)': overall_counts,
        'Osakaal koguajast (%)': overall_pct.round(2)
    })
    overall_df.index.name = 'Kategooria'

    # Hourly overall health analysis
    hourly_overall = df.groupby(['Tund', 'Üldine olek']).size().unstack(fill_value=0)
    hourly_overall = hourly_overall.reindex(columns=overall_categories, fill_value=0)
    hourly_overall_pct = hourly_overall.div(hourly_overall.sum(axis=1), axis=0) * 100

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
        f.write("\nÜLDINE JAOTUS KOGUAJAST\n")
        overall_df.to_csv(f, index=True)
        f.write("\nPROBLEEMIDE JAOTUS (ainult 4 viga, % vigadest)\n")
        summary_df.to_csv(f, index=True)
        f.write("\nTUNNIPÕHINE ANALÜÜS (ainult 4 viga)\n")
        hourly_df.reset_index().to_csv(f, index=False)

    print(f"Writing stats to CSV: {output_csv_stats}...")
    stats_df.to_csv(output_csv_stats, index=False)

    print(f"Writing reasons to CSV: {output_csv_reasons}...")
    summary_df.to_csv(output_csv_reasons, index=True)

    print(f"Writing overall health summary to CSV: {output_csv_yldine_tervis}...")
    overall_df.to_csv(output_csv_yldine_tervis, index=True)

    # --- Daily error breakdown ---
    print("Generating daily error breakdown...")
    df['Kuupäev'] = pd.to_datetime(df['Time']).dt.date
    daily_groups = df.groupby('Kuupäev')

    daily_df = pd.DataFrame()
    daily_df['SOC liiga kõrge'] = daily_groups['Põhjus'].apply(lambda s: (s == 'SOC liiga kõrge').sum())
    daily_df['SOC liiga madal'] = daily_groups['Põhjus'].apply(lambda s: (s == 'SOC liiga madal').sum())
    daily_df['Võrgupiirang'] = daily_groups['Põhjus'].apply(lambda s: (s == 'Võrgupiirang').sum())
    daily_df['Viga - uurimist vajav'] = daily_groups['Põhjus'].apply(lambda s: (s == 'Viga - uurimist vajav').sum())
    daily_df['Vigade koguarv'] = daily_df.sum(axis=1)
    daily_df['Ridade arv'] = daily_groups['Põhjus'].count()

    # Error percentages out of total errors per day
    for col in ['SOC liiga kõrge', 'SOC liiga madal', 'Võrgupiirang', 'Viga - uurimist vajav']:
        daily_df[col + ' (%)'] = (daily_df[col] / daily_df['Vigade koguarv'].replace(0, np.nan) * 100).round(2)

    daily_df.index.name = 'Kuupäev'
    print(f"Writing daily error summary to CSV: {output_csv_daily}...")
    daily_df.reset_index().to_csv(output_csv_daily, index=False)

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
    error_colors = ['#e74c3c', '#e67e22', '#f1c40f', '#9b59b6']

    def save_chart(fig_path_scratch, fig_path_downloads):
        plt.savefig(fig_path_scratch, dpi=150)
        plt.savefig(fig_path_downloads, dpi=150)
        plt.close()

    # 1. Pie Chart - 4 core errors, % from error total
    plt.figure(figsize=(10, 8))
    error_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=error_colors)
    plt.title('Probleemide jaotus (aprill 2026)', fontsize=14, fontweight='bold')
    plt.ylabel('')
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'reason_distribution.png'), output_png_pie)

    # 2. Bar Chart - 4 core errors by hour of day
    plt.figure(figsize=(12, 6))
    hourly_problems = hourly_df[['SOC liiga kõrge', 'SOC liiga madal', 'Võrgupiirang', 'Viga - uurimist vajav']]
    hourly_problems.plot(kind='bar', stacked=True, color=error_colors, ax=plt.gca())
    plt.title('Probleemide esinemine tundide lõikes (aprill 2026)', fontsize=14, fontweight='bold')
    plt.xlabel('Tund (0-23)', fontsize=12)
    plt.ylabel('Probleemide arv', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Probleemi tüüp')
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'problems_by_hour.png'), output_png_hourly)

    # 3. Execution % Timeline
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
    save_chart(os.path.join(charts_dir, 'execution_timeline.png'), output_png_timeline)

    # 4. Daily error timeline (päevade kaupa, 4 viga ajateljel)
    daily_plot = daily_df[['SOC liiga kõrge', 'SOC liiga madal', 'Võrgupiirang', 'Viga - uurimist vajav']]
    plt.figure(figsize=(14, 6))
    for col, color in zip(daily_plot.columns, error_colors):
        plt.plot(daily_df.index, daily_df[col], label=col, color=color, linewidth=2, marker='o', markersize=4)
    plt.title('Probleemide esinemine päevade lõikes (aprill 2026)', fontsize=14, fontweight='bold')
    plt.xlabel('Kuupäev', fontsize=12)
    plt.ylabel('Probleemide arv', fontsize=12)
    plt.legend(title='Probleemi tüüp')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'problems_by_day.png'), output_png_daily_timeline)

    # 5. Overall error share pie chart (% of total error rows)
    plt.figure(figsize=(10, 8))
    error_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=error_colors,
                      wedgeprops=dict(edgecolor='white', linewidth=2))
    plt.title('Probleemide osakaalud kogu perioodi lõikes (ainult vead) (aprill 2026)', fontsize=14, fontweight='bold')
    plt.ylabel('')
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'error_share_pie.png'), output_png_daily_pie)
    
    # 6. Overall health pie chart (Normaalne töö vs problems, and detailed breakdown)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left: 2-slice pie chart (Normaalne töö vs Probleemid kokku)
    health_2_labels = ['Normaalne töö', 'Probleemid kokku']
    health_2_counts = [total_normal, total_errors]
    health_2_colors = ['#2ecc71', '#e74c3c']
    ax1.pie(health_2_counts, labels=health_2_labels, autopct='%1.2f%%', startangle=140,
            colors=health_2_colors, wedgeprops=dict(edgecolor='white', linewidth=2),
            textprops={'fontsize': 12, 'weight': 'bold'})
    ax1.set_title('Süsteemi üldine tööolek koguajast', fontsize=14, fontweight='bold')
    
    # Right: 5-slice pie chart (Normaalne töö + 4 errors)
    health_5_colors = ['#2ecc71', '#f1c40f', '#e74c3c', '#e67e22', '#9b59b6']
    ax2.pie(overall_counts, labels=overall_counts.index, autopct='%1.2f%%', startangle=140,
            colors=health_5_colors, wedgeprops=dict(edgecolor='white', linewidth=1.5),
            textprops={'fontsize': 11})
    ax2.set_title('Kõikide kategooriate osakaal koguajast', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'uldine_tervis_pie.png'), output_png_yldine_pie)

    # 7. Stacked Percentage Bar Chart - Overall health by hour of day
    plt.figure(figsize=(14, 7))
    hourly_overall_pct.plot(kind='bar', stacked=True, color=health_5_colors, ax=plt.gca(), width=0.8)
    plt.title('Süsteemi olekute jaotus tundide lõikes (% koguajast tunnis)', fontsize=14, fontweight='bold')
    plt.xlabel('Tund (0-23)', fontsize=12)
    plt.ylabel('Osakaal (%)', fontsize=12)
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.legend(title='Olek / Probleem', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'uldine_tervis_tundide_kaupa.png'), output_png_yldine_hourly)
    
    print("\n--- ANALYSIS COMPLETED ---")
    print(stats_df.to_string(index=False))
    print("\nÜldine olekute jaotus koguajast:")
    print(overall_df)
    print("\nProbleemide jaotus (4 viga, % vigade koguhulgast):")
    print(summary_df)

if __name__ == '__main__':
    main()
