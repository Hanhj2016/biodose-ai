import sys
from pathlib import Path

# Ensure project root is on sys.path so `src` can be imported when running the script directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.drug_analysis import analyze_drug_response


if __name__ == '__main__':
    sample = PROJECT_ROOT / 'data' / 'examples' / 'drug_response_sample.csv'
    result = analyze_drug_response(str(sample))
    print('Warnings:')
    for w in result['warnings']:
        print('-', w)
    print('\nSummary:')
    print(result['summary_df'].to_string(index=False))
    print('\nCards:')
    print(result['cards'])
