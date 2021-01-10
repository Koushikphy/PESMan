## PESMan
### A program to manage global PES calculations


## Initial Set up:
1. Create Template files for jobs.
2. Modify `pesman.config` file.
3. Modify `geometry.py` file according to the system details and create the object `geomObj`.
4. Modify and run `CreateNewDbs.py` to create the databases relevant to the system type.
5. Modify functions in `ReadResults.py` files for reading results from databases.



## Basic commands:
* Use PESMan `export` to export job.
* Use PESMan `import` to import job after successful run.
* Use PESMan `zip`/`unzip` to archive or extract job folders.
* Use PESMan `delete` to delete any geometry/calculation from database
* Use PESMan `status` anytime to check current status of calculation



## Notes & Tips:
1. `export`/`import` both options support parallel export/import of multiple geometries, just provide the number of process like `-n 4`.
1. Molpro calculation of Calc Ids other than 1 usually doesn't depend on other geometries so, its more efficient to run those jobs in parallel. Specify the option `-par` during export. Number of parallel processes is taken from the `pesman.config`
1. If no `-par` flag is provided or the `RunManager` is used in serial mode, then `proc` value in `pesman.config` is used to run the molpro itself in parallel using its internal MPI implementation.
2. Use `-zip` preferably while importing to archive the data while keeping in GeomData, this will slow down the import/export process, but it heavily reduces file number and sizes. If you don't want to slow down the export/import, you can do the archiving altogether at the end too, using `./PESMan.py zip -all`.
3. Though the neighbour database is created to keep the distances between neighbours, the database itself is never used in any of the calculation.
4. RunManager saves the mcscf iteration numbers in `IterMultiJobs.dat`, and only imports if its below 39 iteration.
5. The `RunManager.py` is used to automatically export/run/import one after other. This can be done with a single job at a time or a bunch of jobs per iteration. As the mcscf is run using information from neighbouring geometries, it is advisable to run those, for initial few jobs in serial. other wise this scirpt can be invoked to run all jobs in bunches of jobs in parallel
6. The RunManager depends on the successfull run of the neighbouring geometries to export a particular job. If a large number of jobs are failed or the database doesn't have enough neighbour information the RunManager sequence can break. In that case, a new job has to be exported manully.
5. To add some new geometries to an existing data base, re-run the `CreateNewDbs.py` by providing the __new complete list of full geometries__. The script will check for existing geometries in the data base and update it with new additional geometries. This will modify all the neighbour geometry information, but won't interfere with any existing results in database.
6. If some calc is semi successful i.e. if like mrci enrgy and ddr are done in a single calc and energy is successful but nact is failed, then run the `collectFailed.py` by providing the `export.dat` as a command-line argument to store the semi successful jobs in a new table in database. This script will also store the result in datafile.
7. Running `python PESMan.py addcalc` for first time will add the calc names and template to the database. If you run the same again with same calc names, PESMan instead of inserting a new calcinfo, will update the existing info template



### Steps to run for H3:
#### Lazy steps, Tl;dr
* specify rho value in `runman.sh` and run it.  
#### Detailed steps
1. Modify `rho` value in CreateNewDps.py and run to create a grid of theta-phi for a fixed value of rho.
2. Run `python PESMan.py addcalc` to add the multi and mrci-ddr calculation information to the database (defined in pesman.config).
3. For first time run `python PESMan.py export -cid 1 -gid 1 -sid 0` to export 1st geometry to run the multi calulation > Run > import it with `PESMan.py import -e ....`
4. Now start RunManager script to do multi calculation for all the geometries sequentially. For first geometries it has to be done one-by-one sequencially, after that it can be run in bunches. Be careful about the depth value in the script. __multi calculation doesn't gain much from parallel running, so just run it in single processor.__
5. Run `./PESMan.py export -cid 2 -j 1000 -n 3 -par` to parallely (3 process) export 1000, calc id 2 i.e. mrci-ddr job > Run > import as 
`PESMan.py import -e <file> -ig wfu -n 3 -zip -del`. `-ig wfu` ignores mrci-ddr wavefunction files during import as they are not necessary to save. Or the better way is to use the `RunManger` again to export/run/import the mrci-nact jobs
6. For H3 template, sometime the energy is done but the nact is failed and pesman can't import the job for that particular geometry, even though the enrgy result is available. In that case run the `collectFailed.py` script to collect such jobs for the job-run directory.
7. At the end run `./PESMan.py zip -all` to archive all data in GeomData folder, if any.