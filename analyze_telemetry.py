import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def aggregate_episodes(df_subset):
    if df_subset.empty:
        cols = [
            'Episoodi ID', 'Põhjus', 'Algusaeg', 'Lõpuaeg', 
            'Kestvus (sekundit)', 'Kestvus (minutit)', 
            'ESS SoC (keskmine)', 'ESS Plan (keskmine)', 
            'PV Power (keskmine)', 'ESS Power (keskmine)', 
            'Grid Power (keskmine)', 'Täitmise % (keskmine)'
        ]
        return pd.DataFrame(columns=cols)
    
    agg_df = df_subset.groupby('Episoodi ID').agg(
        Põhjus=('Põhjus', 'first'),
        Algusaeg=('Time', 'first'),
        Lõpuaeg=('Time', 'last'),
        Kestvus_sekundit=('Episoodi kestvus (sekundit)', 'first'),
        Kestvus_minutit=('Episoodi kestvus (minutit)', 'first'),
        ESS_SoC_keskmine=('ESS SoC', 'mean'),
        ESS_Plan_keskmine=('ESS Plan', 'mean'),
        PV_Power_keskmine=('PV Power', 'mean'),
        ESS_Power_keskmine=('ESS Power', 'mean'),
        Grid_Power_keskmine=('Grid Power', 'mean'),
        Taitmise_pct_keskmine=('Täitmise %', 'mean')
    ).reset_index()
    
    agg_df = agg_df.rename(columns={
        'Kestvus_sekundit': 'Kestvus (sekundit)',
        'Kestvus_minutit': 'Kestvus (minutit)',
        'ESS_SoC_keskmine': 'ESS SoC (keskmine)',
        'ESS_Plan_keskmine': 'ESS Plan (keskmine)',
        'PV_Power_keskmine': 'PV Power (keskmine)',
        'ESS_Power_keskmine': 'ESS Power (keskmine)',
        'Grid_Power_keskmine': 'Grid Power (keskmine)',
        'Taitmise_pct_keskmine': 'Täitmise % (keskmine)'
    })
    
    # Round mean values
    for col in ['ESS SoC (keskmine)', 'ESS Plan (keskmine)', 'PV Power (keskmine)', 
                'ESS Power (keskmine)', 'Grid Power (keskmine)', 'Täitmise % (keskmine)']:
        agg_df[col] = agg_df[col].round(1)
        
    return agg_df.sort_values('Episoodi ID').reset_index(drop=True)

def main(date_arg=None):
    if date_arg:
        date_arg = date_arg.strip()
        if not date_arg or date_arg.lower() == 'none':
            date_arg = None
            
    csv_path = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_combined.csv'
    
    # Summary CSV Outputs
    output_csv_summary = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary.csv'
    output_csv_stats = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_stats.csv'
    output_csv_reasons = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_reasons.csv'
    output_csv_daily = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_errors_by_date.csv'
    output_csv_yldine_tervis = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_yldine_tervis.csv'
    output_csv_summary_episodes = '/Users/user/Downloads/raw_telemetry_2ccf67f82f80_summary_episoodid.csv'

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

    # --- Group consecutive rows into episodes and calculate durations ---
    print("Grouping consecutive rows into episodes...")
    df = df.sort_values('Time').reset_index(drop=True)
    df['Time_dt'] = pd.to_datetime(df['Time'])
    
    # Time diff in seconds
    time_diffs = df['Time_dt'].diff().dt.total_seconds()
    
    # An episode is consecutive rows with same Põhjus and time gap <= 30s
    new_episode = (df['Põhjus'] != df['Põhjus'].shift(1)) | (time_diffs > 30)
    df['Episoodi ID'] = new_episode.cumsum()
    
    # Calculate durations per episode
    episode_bounds = df.groupby('Episoodi ID')['Time_dt'].agg(['min', 'max'])
    episode_durations = (episode_bounds['max'] - episode_bounds['min']).dt.total_seconds() + 25
    
    # Map back to rows
    df['Episoodi kestvus (sekundit)'] = df['Episoodi ID'].map(episode_durations).astype(int)
    df['Episoodi kestvus (minutit)'] = (df['Episoodi kestvus (sekundit)'] / 60).round(2)

    # Save datetime column for plotting later before cleanup
    time_dt_series = df['Time_dt']
    df = df.drop(columns=['Time_dt'])
    
    # Reorder columns
    cols = [
        'Time', 'ESS SoC', 'ESS Plan', 'PV Power', 'ESS Power', 'Grid Power', 
        'Täitmise %', 'Põhjus', 'Tund', 'Episoodi ID', 
        'Episoodi kestvus (sekundit)', 'Episoodi kestvus (minutit)'
    ]
    df = df[cols]

    # --- Write Separate CSV Files (using detailed classifications, aggregated by episode) ---
    print("Writing separate CSV files for each category (aggregated by episode)...")
    
    aggregate_episodes(df[df['Põhjus'] == 'SOC liiga kõrge']).to_csv(output_csv_soc_korge, index=False)
    aggregate_episodes(df[df['Põhjus'] == 'SOC liiga madal']).to_csv(output_csv_soc_madal, index=False)
    aggregate_episodes(df[df['Põhjus'] == 'Võrgupiirang']).to_csv(output_csv_vorgupiirang, index=False)
    aggregate_episodes(df[df['Põhjus'] == 'Osaline täitmine']).to_csv(output_csv_osaline_taitmine, index=False)
    aggregate_episodes(df[df['Põhjus'] == 'Ootamatu reageering']).to_csv(output_csv_ootamatu_reageering, index=False)
    aggregate_episodes(df[df['Põhjus'] == 'Viga - uurimist vajav']).to_csv(output_csv_uurimist_vajav, index=False)

    # --- Map Non-Critical Categories for summaries and charts ---
    print("Merging non-critical classifications (Osaline täitmine -> Käsk täidetud, Ootamatu reageering -> Käsku ei antud)...")
    df['Põhjus'] = df['Põhjus'].replace({
        'Osaline täitmine': 'Käsk täidetud',
        'Ootamatu reageering': 'Käsku ei antud'
    })

    # Define overall health states
    df['Üldine olek'] = df['Põhjus'].apply(lambda x: 'Normaalne töö' if x in ['Käsk täidetud', 'Käsku ei antud'] else x)

    # Calculate overall episodes based on mapped 'Üldine olek' and time gaps
    df['Time_dt'] = pd.to_datetime(df['Time'])
    time_diffs = df['Time_dt'].diff().dt.total_seconds()
    new_episode_overall = (df['Üldine olek'] != df['Üldine olek'].shift(1)) | (time_diffs > 30)
    df['Episoodi ID Üldine'] = new_episode_overall.cumsum()

    # Aggregate overall health episodes
    overall_episodes_bounds = df.groupby('Episoodi ID Üldine')['Time_dt'].agg(['first', 'last'])
    overall_episodes_df = pd.DataFrame({
        'Episoodi ID': overall_episodes_bounds.index,
        'Üldine olek': df.groupby('Episoodi ID Üldine')['Üldine olek'].first(),
        'Algusaeg': overall_episodes_bounds['first'],
        'Lõpuaeg': overall_episodes_bounds['last']
    }).reset_index(drop=True)

    # Calculate episode durations
    overall_episodes_df['Kestvus (sekundit)'] = (overall_episodes_df['Lõpuaeg'] - overall_episodes_df['Algusaeg']).dt.total_seconds() + 25
    overall_episodes_df['Kestvus (sekundit)'] = overall_episodes_df['Kestvus (sekundit)'].astype(int)
    overall_episodes_df['Kestvus (minutit)'] = (overall_episodes_df['Kestvus (sekundit)'] / 60).round(2)
    overall_episodes_df['Tund'] = overall_episodes_df['Algusaeg'].dt.hour
    overall_episodes_df['Kuupäev'] = overall_episodes_df['Algusaeg'].dt.date

    # --- Generate Summary Statistics (only 4 core errors) ---
    print("Generating Summary Statistics...")
    error_categories = [
        'SOC liiga kõrge',
        'SOC liiga madal',
        'Võrgupiirang',
        'Viga - uurimist vajav'
    ]
    
    # Filter overall episodes for the 4 core error categories
    error_episodes_df = overall_episodes_df[overall_episodes_df['Üldine olek'].isin(error_categories)]
    error_counts = error_episodes_df['Üldine olek'].value_counts().reindex(error_categories, fill_value=0)
    total_error_incidents = error_counts.sum()
    error_pct = (error_counts / total_error_incidents) * 100 if total_error_incidents > 0 else 0

    summary_df = pd.DataFrame({
        'Juhtumite arv (episoodid)': error_counts,
        'Osakaal vigadest (%)': error_pct.round(2)
    })
    summary_df.index.name = 'Probleem'

    total_incidents = len(overall_episodes_df)
    total_normal_incidents = (overall_episodes_df['Üldine olek'] == 'Normaalne töö').sum()
    
    stats_df = pd.DataFrame({
        'Näitaja': [
            'Juhtumite koguarv (episoodid)',
            'Toimib nagu peab (Normaalne töö juhtumid)',
            'Vigade koguarv (4 probleemi juhtumid)',
            'SOC liiga kõrge juhtumid',
            'SOC liiga madal juhtumid',
            'Võrgupiirang juhtumid',
            'Viga - uurimist vajav juhtumid',
            'Normaalne töö osakaal juhtumitest (%)',
            'Vigade osakaal juhtumitest (%)',
        ],
        'Väärtus': [
            total_incidents,
            int(total_normal_incidents),
            int(total_error_incidents),
            int(error_counts['SOC liiga kõrge']),
            int(error_counts['SOC liiga madal']),
            int(error_counts['Võrgupiirang']),
            int(error_counts['Viga - uurimist vajav']),
            round((total_normal_incidents / total_incidents) * 100, 2) if total_incidents > 0 else 0,
            round((total_error_incidents / total_incidents) * 100, 2) if total_incidents > 0 else 0,
        ]
    })

    # --- Generate Overall Health Distribution (based on episode duration sum) ---
    print("Generating Overall Health Distribution...")
    overall_categories = [
        'Normaalne töö',
        'Võrgupiirang',
        'SOC liiga kõrge',
        'SOC liiga madal',
        'Viga - uurimist vajav'
    ]
    
    # Calculate duration sum per overall category
    overall_durations = overall_episodes_df.groupby('Üldine olek')['Kestvus (sekundit)'].sum().reindex(overall_categories, fill_value=0)
    total_duration = overall_durations.sum()
    overall_pct = (overall_durations / total_duration) * 100 if total_duration > 0 else 0

    overall_df = pd.DataFrame({
        'Kestvuse summa (tundi)': (overall_durations / 3600).round(2),
        'Osakaal koguajast (%)': overall_pct.round(2)
    })
    overall_df.index.name = 'Kategooria'

    # Hourly overall health analysis based on telemetry rows (represents exact time share per hour)
    hourly_overall = df.groupby(['Tund', 'Üldine olek']).size().unstack(fill_value=0)
    hourly_overall = hourly_overall.reindex(index=range(24), fill_value=0)
    hourly_overall = hourly_overall.reindex(columns=overall_categories, fill_value=0)
    hourly_overall_pct = hourly_overall.div(hourly_overall.sum(axis=1), axis=0) * 100
    hourly_overall_pct = hourly_overall_pct.fillna(0)

    # --- Hourly Analysis (only 4 core errors) ---
    print("Generating Hourly Analysis...")
    hourly_df = pd.DataFrame(index=range(24))
    hourly_df.index.name = 'Tund'

    for cat in error_categories:
        cat_counts = error_episodes_df[error_episodes_df['Üldine olek'] == cat].groupby('Tund').size()
        hourly_df[cat] = cat_counts.reindex(range(24), fill_value=0)
        
    hourly_df['Vigade koguarv tunnis'] = hourly_df[error_categories].sum(axis=1)

    # --- Generate Episode Statistics (only 4 core errors) ---
    print("Generating Episode Statistics...")
    episode_stats = []
    for cat in error_categories:
        cat_episodes = error_episodes_df[error_episodes_df['Üldine olek'] == cat]
        num_incidents = len(cat_episodes)
        if num_incidents > 0:
            total_sec = cat_episodes['Kestvus (sekundit)'].sum()
            avg_sec = cat_episodes['Kestvus (sekundit)'].mean()
            max_sec = cat_episodes['Kestvus (sekundit)'].max()
        else:
            total_sec = 0
            avg_sec = 0
            max_sec = 0
            
        episode_stats.append({
            'Probleem': cat,
            'Juhtumite arv (episoodid)': num_incidents,
            'Kokku kestvus (sekundit)': int(total_sec),
            'Kokku kestvus (tundi)': round(total_sec / 3600, 2),
            'Keskmine kestvus (sekundit)': round(avg_sec, 1),
            'Maksimaalne kestvus (sekundit)': int(max_sec)
        })
    episode_summary_df = pd.DataFrame(episode_stats)

    # --- Write Outputs to Downloads ---
    print(f"Writing combined summary to CSV: {output_csv_summary}...")
    with open(output_csv_summary, 'w', encoding='utf-8') as f:
        f.write("ÜLDINE STATISTIKA\n")
        stats_df.to_csv(f, index=False)
        f.write("\nÜLDINE JAOTUS KOGUAJAST\n")
        overall_df.to_csv(f, index=True)
        f.write("\nPROBLEEMIDE JUHTUMID (EPISOODID) JA KESTVUSED\n")
        episode_summary_df.to_csv(f, index=False)
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

    print(f"Writing episode summary to CSV: {output_csv_summary_episodes}...")
    episode_summary_df.to_csv(output_csv_summary_episodes, index=False)

    # --- Daily error breakdown ---
    print("Generating daily error breakdown...")
    df['Kuupäev'] = pd.to_datetime(df['Time']).dt.date
    all_dates = sorted(df['Kuupäev'].unique())
    
    daily_df = pd.DataFrame(index=all_dates)
    daily_df.index.name = 'Kuupäev'
    
    for cat in error_categories:
        cat_daily = error_episodes_df[error_episodes_df['Üldine olek'] == cat].groupby('Kuupäev').size()
        daily_df[cat] = cat_daily.reindex(all_dates, fill_value=0)
        
    daily_df['Vigade koguarv'] = daily_df[error_categories].sum(axis=1)
    
    total_daily_episodes = overall_episodes_df.groupby('Kuupäev').size()
    daily_df['Juhtumite koguarv'] = total_daily_episodes.reindex(all_dates, fill_value=0)
    
    # Error percentages out of total errors per day
    for col in error_categories:
        daily_df[col + ' (%)'] = (daily_df[col] / daily_df['Vigade koguarv'].replace(0, np.nan) * 100).round(2)
        daily_df[col + ' (%)'] = daily_df[col + ' (%)'].fillna(0.0)
        
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
    plt.title('Probleemide jaotus juhtumite põhjal (aprill 2026)', fontsize=14, fontweight='bold')
    plt.ylabel('')
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'reason_distribution.png'), output_png_pie)

    # 2. Bar Chart - 4 core errors by hour of day
    plt.figure(figsize=(12, 6))
    hourly_problems = hourly_df[['SOC liiga kõrge', 'SOC liiga madal', 'Võrgupiirang', 'Viga - uurimist vajav']]
    hourly_problems.plot(kind='bar', stacked=True, color=error_colors, ax=plt.gca())
    plt.title('Probleemide (intsidentide) algusajad tundide lõikes (aprill 2026)', fontsize=14, fontweight='bold')
    plt.xlabel('Tund (0-23)', fontsize=12)
    plt.ylabel('Juhtumite arv', fontsize=12)
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
    plt.title('Probleemide esinemine päevade lõikes (juhtumite arv, aprill 2026)', fontsize=14, fontweight='bold')
    plt.xlabel('Kuupäev', fontsize=12)
    plt.ylabel('Juhtumite arv', fontsize=12)
    plt.legend(title='Probleemi tüüp')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'problems_by_day.png'), output_png_daily_timeline)

    # 5. Overall error share pie chart (% of total error incidents)
    plt.figure(figsize=(10, 8))
    error_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=error_colors,
                      wedgeprops=dict(edgecolor='white', linewidth=2))
    plt.title('Probleemide osakaalud kogu perioodi lõikes (ainult vead, juhtumite arv) (aprill 2026)', fontsize=14, fontweight='bold')
    plt.ylabel('')
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'error_share_pie.png'), output_png_daily_pie)
    
    # 6. Overall health pie chart (Normaalne töö vs problems, and detailed breakdown)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left: 2-slice pie chart (Normaalne töö vs Probleemid kokku)
    health_2_labels = ['Normaalne töö', 'Probleemid kokku']
    health_2_counts = [overall_durations['Normaalne töö'], overall_durations[error_categories].sum()]
    health_2_colors = ['#2ecc71', '#e74c3c']
    ax1.pie(health_2_counts, labels=health_2_labels, autopct='%1.2f%%', startangle=140,
            colors=health_2_colors, wedgeprops=dict(edgecolor='white', linewidth=2),
            textprops={'fontsize': 12, 'weight': 'bold'})
    ax1.set_title('Süsteemi üldine tööolek (kestvuse järgi)', fontsize=14, fontweight='bold')
    
    # Right: 5-slice pie chart (Normaalne töö + 4 errors)
    health_5_colors = ['#2ecc71', '#f1c40f', '#e74c3c', '#e67e22', '#9b59b6']
    ax2.pie(overall_durations, labels=overall_durations.index, autopct='%1.2f%%', startangle=140,
            colors=health_5_colors, wedgeprops=dict(edgecolor='white', linewidth=1.5),
            textprops={'fontsize': 11})
    ax2.set_title('Kõikide kategooriate osakaal (kestvuse järgi)', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'uldine_tervis_pie.png'), output_png_yldine_pie)

    # 7. Stacked Percentage Bar Chart - Overall health by hour of day
    plt.figure(figsize=(14, 7))
    hourly_overall_pct.plot(kind='bar', stacked=True, color=health_5_colors, ax=plt.gca(), width=0.8)
    plt.title('Süsteemi olekute jaotus tundide lõikes (% ajalisest kestvusest tunnis)', fontsize=14, fontweight='bold')
    plt.xlabel('Tund (0-23)', fontsize=12)
    plt.ylabel('Osakaal (%)', fontsize=12)
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.legend(title='Olek / Probleem', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    save_chart(os.path.join(charts_dir, 'uldine_tervis_tundide_kaupa.png'), output_png_yldine_hourly)
    
    # --- Optional Day-Specific Analysis (if date_arg is provided) ---
    if date_arg:
        print(f"Generating date-specific analysis for: {date_arg}...")
        df['Kuupäev'] = pd.to_datetime(df['Time']).dt.date
        available_dates = df['Kuupäev'].astype(str).unique()
        if date_arg not in available_dates:
            print(f"Warning: Date {date_arg} not found in dataset. Available dates: {sorted(available_dates)}")
        else:
            # Filter error episodes for this date
            day_episodes = error_episodes_df[error_episodes_df['Kuupäev'].astype(str) == date_arg]
            
            # Group by hour and category
            day_hourly = day_episodes.groupby(['Tund', 'Üldine olek']).size().unstack(fill_value=0)
            # Reindex with the 24 hours and the 4 error categories
            day_hourly = day_hourly.reindex(index=range(24), fill_value=0)
            day_hourly = day_hourly.reindex(columns=error_categories, fill_value=0)
            
            # Generate the chart
            plt.figure(figsize=(12, 6))
            day_hourly.plot(kind='bar', stacked=True, color=error_colors, ax=plt.gca())
            plt.title(f'Probleemide esinemine tundide lõikes kuupäeval {date_arg} (juhtumite arv)', fontsize=14, fontweight='bold')
            plt.xlabel('Tund (0-23)', fontsize=12)
            plt.ylabel('Probleemide arv (juhtumid)', fontsize=12)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.legend(title='Probleemi tüüp')
            plt.tight_layout()
            
            # Save paths
            output_png_day = f'/Users/user/Downloads/raw_telemetry_2ccf67f82f80_chart_paevapohine_{date_arg}.png'
            scratch_png_day = os.path.join(charts_dir, f'uldine_tervis_paevapohine_{date_arg}.png')
            save_chart(scratch_png_day, output_png_day)
            print(f"Saved day-specific chart to {output_png_day}")
            
    print("\n--- ANALYSIS COMPLETED ---")
    print(stats_df.to_string(index=False))
    print("\nÜldine olekute jaotus koguajast:")
    print(overall_df)
    print("\nProbleemide jaotus (4 viga, % vigade koguhulgast):")
    print(summary_df)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Battery Telemetry Analysis")
    parser.add_argument('--date', type=str, help="Specific date for hourly analysis (YYYY-MM-DD)", default=None)
    args = parser.parse_args()
    main(args.date)
