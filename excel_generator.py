# excel_generator.py
import logging
import pandas as pd
logger = logging.getLogger(__name__)
class ExcelGenerator:
    def __init__(self, output_filepath):
        self.output_filepath = output_filepath
    def create_report(self, data):
        if not data:
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(data)
        try:
            with pd.ExcelWriter(self.output_filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='QA_Report', index=False)
        except Exception as e:
            logger.error(f"Failed to create Excel report: {e}")
            raise