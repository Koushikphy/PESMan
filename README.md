## PESMan
### A program to manage global PES calculations


## Initial Set up:
1. Create Template files for jobs.
2. Modify `pesman.config` file.
3. Modify `geometry.py` file according to the system details and create the object `geomObj`.
4. Modify and run `CreateNewDbs.py` to create the databases.
5. Modify `ReadResultsMulti.py` and `ReadResultsNacts.py` files for reading results from databases.

## Usage:
* Initial setup
* Use PESMan `export` to export job.
* Use PESMan `import` to import job after successful run.
* Use `RunManager.py` to sequencially export and import.
* Use PESMan `zip`/`unzip` to archive or extract job folders.