# CITS1401 Project Semester 1, 2026
# David Bejan,  25310062

def std_dev(values):
    """Calculate sample standard deviation (N-1 in denominator).
    
    Args:
        values: list of numbers.
    
    Returns:
        Sample standard deviation as a float. Returns 0.0 if fewer than 2 values.
    """
    n = len(values)
    if n <= 1:
        return 0.0
    mean = sum(values) / n

    total = 0
    for v in values:
        total += (v - mean) ** 2

    return (total / (n-1)) ** 0.5

def cosine_similarity(vec_a, vec_b):
    """Calculate cosine similarity between two equal-length numeric vectors.
    
    Args:
        vec_a, vec_b: lists of numbers, same length.
    
    Returns:
        Cosine similarity as a float. Returns 0.0 if either vector has
        zero magnitude (to avoid division by zero).
    """
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = sum(a ** 2 for a in vec_a) ** 0.5
    mag_b = sum(b ** 2 for b in vec_b) ** 0.5
    
    if mag_a == 0 or mag_b == 0:
        return 0.0
    
    return dot / (mag_a * mag_b)

def parse_header(line):
    """Build a dict mapping column names (uppercased) to their position index.
      
    Args:
      line: the header row from the CSV file (string).
      
    Returns:
        Dict mapping each column name (uppercased and stripped) to its 0-based
        column index in the file.
    """
    col_idx = {}
    header = line.strip().split(',')
    for i, name in enumerate(header):
        col_idx[name.strip().upper()] = i

    return col_idx

def dict_traffic_year(region_rows):
    """Build OP1: per-year summary statistics for traffic count sites.

    For each TRAFFIC_YEAR present in the input rows, computes:
    site count, average MON_SUN, sample std dev of MON_SUN, and the
    SITE_NO of the row with highest PCT_HEAVY_MON_SUN (alphabetical
    tiebreak by GlobalID).

    Args:
        region_rows: list of validated row dicts, already filtered to
            the target administrative region. Each row must contain at
            least TRAFFIC_YEAR, MON_SUN, PCT_HEAVY_MON_SUN, SITE_NO,
            and GLOBALID keys.

    Returns:
        Dict mapping each year (str) to a 4-element list:
            [count (int), avg_mon_sun (float), std_mon_sun (float), best_site_no (str)]
        Numeric values are rounded to 4 decimal places.
        Returns an empty dict if region_rows is empty.
    """
    year_map = {}
    for row in region_rows:
        yr = row['TRAFFIC_YEAR']
        year_map.setdefault(yr, []).append(row)
    
    op1 = {}
    for yr, rows in year_map.items():
        n = len(rows)
        mon_sun_values =[r['MON_SUN'] for r in rows]
        avg = sum(mon_sun_values) / n
        std = std_dev(mon_sun_values)

        sorted_rows = sorted(rows, key= lambda r: (-r['PCT_HEAVY_MON_SUN'], r['GLOBALID'].lower()))
        best_site = str(sorted_rows[0]['SITE_NO'])

        op1[yr] = [n, round(avg, 4), round(std, 4), best_site]

    return op1

def dict_lg_sites(region_rows):
    """Build OP2: traffic count site summary with respect to all day volume and local govt area 
    
    For each LG_NAME (local government area) present in the input rows,
    it ranks every local govt area with at least 3 sites in terms of 
    highest MON_SUN traffic volume (GLOBALID tiebreaker) and assigns
    SITE_NO, MON_SUN, and PCT_HEAVY_MON_SUN along with the rank.
    
    Args:
        region_rows: list of validated row dicts, already filtered to
        the target administrative region. Each row must contain at
        least LG_NAME, MON_SUN, GLOBALID, SITE_NO and PCT_HEAVY_MON_SUN

    Returns:
       Nested dict.
            Outer key: LG_NAME (lowercased string).
            Outer value: inner dict mapping SITE_NO (string) to a
                3-element list [MON_SUN, PCT_HEAVY_MON_SUN, rank].
            Numeric values are rounded to 4 decimal places.
        Returns an empty dict if no LG within the region contains at
        least 3 valid sites.
    """
    
    lg_map = {}
    for row in region_rows:
        lg = row['LG_NAME'].strip().lower()
        lg_map.setdefault(lg, []).append(row)
    
    op2 = {}
    for lg, rows in lg_map.items():
        if len(rows) < 3:
            continue

        sorted_rows = sorted(rows, key= lambda r: (-r['MON_SUN'], r['GLOBALID'].lower()))

        inner = {}
        for rank, row in enumerate(sorted_rows, start= 1):
            inner[str(row['SITE_NO'])] = [
                round(row['MON_SUN'], 4),
                round(row['PCT_HEAVY_MON_SUN'], 4),
                rank
            ]

        op2[lg] = inner
   
    return op2

def traffic_lst(region_rows):
    """Build OP3: per-year heavy-vehicle averages and their cosine similarity.
      
    For each TRAFFIC_YEAR present in the input rows, computes the mean
    weekday heavy-vehicle percentage (PCT_HEAVY_MON_FRI) and the mean
    weekend percentage (PCT_HEAVY_SAT_SUN). Both vectors use the same
    chronologically-ordered set of years.
      
    Args:
        region_rows: list of validated row dicts, already filtered to
        the target administrative region.
      
    Returns:
        3-element list:
            [0]: weekday averages, one per year (list of floats).
            [1]: weekend averages, one per year (list of floats).
            [2]: cosine similarity between [0] and [1] (float).
        Numeric values are rounded to 4 decimal places.
        Returns an empty list if region_rows is empty.
    """
    if not region_rows:
        return []
    
    year_map = {}
    for row in region_rows:
        yr = row['TRAFFIC_YEAR']
        year_map.setdefault(yr, []).append(row)
    
    sorted_years = sorted(year_map.keys())
    
    weekday_avg = []
    weekend_avg = []

    for yr in sorted_years:
        rows = year_map[yr]
        weekday_avg.append(sum(r['PCT_HEAVY_MON_FRI'] for r in rows) / len(rows))
        weekend_avg.append(sum(r['PCT_HEAVY_SAT_SUN'] for r in rows) / len(rows))

    cos_sim = cosine_similarity(weekday_avg, weekend_avg)

    op3 = [
        [round(v, 4) for v in weekday_avg],
        [round(v, 4) for v in weekend_avg],
        round(cos_sim, 4)
    ]

    return op3

def main(file_name, ra_name):
    """Analyse WA traffic count data for one administrative region.
    
    Reads a CSV file, filters out invalid rows (missing/non-numeric/
    negative values, duplicate SITE_NO), filters to the requested RA,
    and computes three summary outputs.
    
    Args:
        file_name: path to the CSV file (string).
        ra_name: name of the administrative region (string,
            case-insensitive).
    
    Returns:
        Tuple (OP1, OP2, OP3):
            OP1: dict keyed by TRAFFIC_YEAR with [count, avg, std, site_no] values.
            OP2: nested dict, outer key LG_NAME, inner key SITE_NO,
                 value [mon_sun, pct_heavy_mon_sun, rank].
            OP3: list [weekday_pct_avgs, weekend_pct_avgs, cosine_similarity].
        Returns ({}, {}, []) on file-not-found or if no valid rows match.
    """
    if not isinstance(file_name, str) or not isinstance(ra_name, str):
        return {}, {}, []
    
    try:
        with open(file_name, 'r') as f:
            lines = f.readlines() 
    except (OSError, UnicodeDecodeError):
        return {}, {}, []

    if len(lines) < 2:
        return {}, {}, []

    col_idx = parse_header(lines[0])

    required = ['SITE_NO', 'RA_NAME', 'LG_NAME', 'TRAFFIC_YEAR', 'GLOBALID',
            'MON_SUN', 'PCT_HEAVY_MON_SUN', 'PCT_HEAVY_MON_FRI', 'PCT_HEAVY_SAT_SUN']
    
    for col in required:
        if col not in col_idx:
            return {}, {}, []

    candidates = []

    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        parts = line.split(',')
        if len(parts) < len(col_idx):
            continue

        valid = True    
        row = {}

        for col in ['SITE_NO', 'RA_NAME', 'LG_NAME', 'TRAFFIC_YEAR', 'GLOBALID']:
            val = parts[col_idx[col]].strip()
            if not val:
                valid = False
                break
            row[col] = val

        if not valid:
            continue

        for col in ['MON_SUN', 'PCT_HEAVY_MON_SUN', 'PCT_HEAVY_MON_FRI', 'PCT_HEAVY_SAT_SUN']:
            val = parts[col_idx[col]].strip()
            if not val:
                valid = False
                break

            try:
                num = float(val)
            except ValueError:
                valid = False
                break

            if num < 0:
                valid = False
                break

            row[col] = num

        if not valid:
            continue
        
        candidates.append(row)

    site_no_counts = {}
    for row in candidates:
        s_no = row['SITE_NO']
        site_no_counts[s_no] = site_no_counts.get(s_no, 0) + 1
    
    unique_rows = []
    for row in candidates:
        if site_no_counts[row['SITE_NO']] == 1:
            unique_rows.append(row)

    ra_lower = ra_name.strip().lower()
    region_rows = [row for row in unique_rows 
                   if row['RA_NAME'].strip().lower() == ra_lower] 

    if not region_rows:
        return {},{}, []

    return dict_traffic_year(region_rows), dict_lg_sites(region_rows), traffic_lst(region_rows)