## PESMan
### A program to manage global PES calculations


## Initial Set up:
1. Create Template files for jobs.
2. Modify `pesman.config` file.
3. Modify `geometry.py` file according to the system details and create the object `geomObj`.
4. Modify and run `CreateNewDbs.py` to create the databases relevant to the system type.
5. Modify `main` function in `ReadResults.py` files for reading results from databases.

## Usage:
* Use PESMan `export` to export job.
* Use PESMan `import` to import job after successful run.
* Use `RunManager.py` to sequencially export and import.
* Use PESMan `zip`/`unzip` to archive or extract job folders.
* Use PESMan `delete` to delete any geometry/calculation from database
* Use PESMan `status` to check current status of calculation