"""Dummy job recipe for testing purposes."""

import os
import json
from mkite_core.models import JobInfo
from mkite_core.recipes import BaseRecipe


class DummyRecipe(BaseRecipe):
    """A simple dummy recipe that creates a test output file."""
    
    def __init__(self, job_info: JobInfo):
        super().__init__(job_info)
    
    def run(self):
        """Run the dummy job - just create a simple output file."""
        # Create a dummy output file to simulate job completion
        output_data = {
            "job_id": str(self.job_info.job),
            "recipe": self.job_info.recipe.get("name", "dummy"),
            "status": "completed",
            "message": "Dummy job completed successfully"
        }
        
        with open("dummy_output.json", "w") as f:
            json.dump(output_data, f, indent=2)
        
        # Create a completion marker file
        with open("job_complete.txt", "w") as f:
            f.write("Job completed successfully\n")
        
        return output_data
