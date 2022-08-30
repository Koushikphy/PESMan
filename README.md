## PESMan
### A program to manage global PES calculations


## Basic commands:
* Use PESMan `export` to export job.
* Use PESMan `import` to import job after successful run.
* Use PESMan `zip`/`unzip` to archive or extract job folders.
* Use PESMan `delete` to delete any geometry/calculation from database
* Use PESMan `status` anytime to check current status of calculation


## Initial Set up:
1. Create Molpro template (`*.template`) files for jobs.
2. Modify `pesman.config` file with necessary information and template names.
3. Modify `geometry.py` file according to the system details and create the object `geomObj`.
4. Modify `CreateNewDbs.py` corresponding to the system details and grid required and run to create the databases relevant to the system type.
5. Modify `ReadResults.py` file for reading results from databases.
6. Run `python PESMan.py addcalc` to add the calculation defined in the `pesman.config`.
7. Now we are ready to start the _ab intio_ jobs. For first time run `python PESMan.py export -cid 1 -gid 1 -sid 0` to export 1st geometry for calcid 1 without any starting geometry (`-sid 0`). Run the job file (`RunJob*.py`) created inside the `ExpDir`. Upon successful run import it with `PESMan.py import -e <path to export.dat>`
8. Now the `RunManager` script can do the calculations for all the geometries sequentially. For first geometries in multi calculation it has to be done one-by-one sequentially to accumulate enough seed geometry, after that it can be run in bunches. Be careful about the depth value in the script. Tweak the different parameters in `RunManager` to get better performance. Note, `RunManager` also calls the `ReadResults` script to periodically to extract the results from database and store it in a datafile.
9. Manual export/import can also be done. Run `./PESMan.py export -cid 2 -j 1000 -n 3 -par` to parallel (3 process) export 1000 for calc id 2 > Run > import as `PESMan.py import -e <export.dat file> -ig wfu -n 3 -zip -del`. `-ig wfu` ignores wavefunction files during import. But its recommended to use the `RunManager` script instead.
10. Run `./PESMan.py status` at any moment to check the current status of the calculation.



## Notes & Tips:
1. Molpro calculation of Calc Ids other than 1 usually doesn't depend on other geometries so, its more efficient to run those jobs in parallel. Specify the option `-par` during export. Number of parallel processes is taken from the `pesman.config`
1. If no `-par` flag is provided or the `RunManager` is used in serial mode, then `proc` value in `pesman.config` is used to run the Molpro itself in parallel using its internal MPI implementation.
2. Use `-zip` preferably while importing to archive the data while keeping in `GeomData`, this will slow down the import/export process, but it heavily reduces file number and sizes. If you don't want to slow down the export/import, you can do the archiving altogether at the end too, using `./PESMan.py zip -all`.
3. Though the neighbor database is created to keep the distances between neighbors, the database itself is never used in any of the calculation.
4. RunManager saves the mcscf iteration numbers in `IterMultiJobs.dat`, and only imports if its below 39 iteration.
5. The `RunManager.py` is used to automatically export/run/import one after other. This can be done with a single job at a time or a bunch of jobs per iteration. As the mcscf is run using information from neighboring geometries, it is advisable to run those, for initial few jobs in serial. other wise this script can be invoked to run all jobs in bunches of jobs in parallel
6. The RunManager depends on the successful run of the neighboring geometries to export a particular job. If a large number of jobs are failed or the database doesn't have enough neighbor information the RunManager sequence can break. In that case, RunManager searches globally for the closest neighbor pair of incomplete jobs, and performs a brute-force export to keep the job going. If that fails, a new job has to be exported manually.
5. If some calculation has to be removed, Run the `./PESMan.py delete` with `calcId` and `geomId` to remove that from the database.
5. To add some new geometries to an existing data base, re-run the `CreateNewDbs.py` by providing the __new complete list of full geometries__. The script will check for existing geometries in the data base and update it with new additional geometries. This will modify all the neighbor geometry information, but won't interfere with any existing results in database.
6. If some calc is semi successful i.e. if like mrci energy and ddr are done in a single calc and energy is successful but nact is failed, then run the `collectFailed.py` by providing the `export.dat` as a command-line argument to store the semi successful jobs in a new table in database. This script will also store the result in datafile.
7. Running `python PESMan.py addcalc` for first time will add the calc names and template to the database. If you run the same again with same calc names, PESMan instead of inserting a new calcinfo, will update the existing info template

