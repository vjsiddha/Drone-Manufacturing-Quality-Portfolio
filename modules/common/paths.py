from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data"
REPORTS_DIR = ROOT_DIR / "reports"
ASSETS_DIR = ROOT_DIR / "assets"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

NCR_DB_PATH = DATA_DIR / "ncr_capa.db"

FMEA_CSV = DATA_DIR / "propulsion_fmea.csv"
FMEA_XLSX = DATA_DIR / "propulsion_fmea.xlsx"

INSPECTION_REQUIREMENTS = DATA_DIR / "inspection_requirements.yaml"
SAMPLE_MEASUREMENTS = DATA_DIR / "sample_measurements.csv"
INSPECTION_RESULTS = DATA_DIR / "inspection_results.csv"
DRAFT_NCRS = DATA_DIR / "draft_ncrs.csv"

PRODUCTION_RECORDS = DATA_DIR / "production_records.csv"
INSPECTION_RECORDS = DATA_DIR / "inspection_records.csv"
NCR_RECORDS = DATA_DIR / "ncr_records.csv"
SUPPLIERS = DATA_DIR / "suppliers.csv"
PARTS = DATA_DIR / "parts.csv"
SPC_MEASUREMENTS = DATA_DIR / "spc_measurements.csv"