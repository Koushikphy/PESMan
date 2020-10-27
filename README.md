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
1. Initial mulit calculation is done by taking initial guess from neighobouring geometries. The `RunManager.py` is used for this purpose.
After few (50-100) initial geometries are done sequentially and serially, parallel `RunManager` can be invoked by changing the `process` value in the script to more than `1`, value `1` meaning serial execution. In that case, the script will export a bunch of jobs from the neighbourhood of successful geometries and run them in parallel.
1. `export`/`import` both options support parallel export/import of multiple geometries, just provide the number of process like `-n 4`.
1. Molpro calculation of Calc Ids other than 1 usually doesn't depend on other geometries so, its more efficient to run those jobs in parallel. Specify the option `-par` during export. Number of parallel processes is taken from the `pesman.config`
1. If no `-par` flag is provided or the `RunManager` is used in serial mode, then `proc` value in `pesman.config` is used to run the molpro itself in parallel using its internal MPI implementation.
2. Use `-zip` preferably while importing to archive the data while keeping in GeomData, this will slow down the import/export process, but it heavily reduces file number and sizes. If you don't want to slow down the export/import, you can do the archiving altogether at the end too, using `./PESMan.py zip -all`.
3. Though the neighbour database is created to keep the distances between neighbours, the database itself is never used in any of the calculation.
4. RunManager saves the mcscf iteration numbers in `IterMultiJobs.dat`, and only imports if its below 39 iteration.
4. The `RunManager` by default moves exported job to RunDir for execution and import it directly from there, it doesn't use the ImpDir folder.
5. `RunManager` exports a job to `ExpDir` copies it to `RunDir` and run there. If the job is successful it deletes job directory both from `ExpDir` and `RunDir`, otherwise keeps it.
6. The RunManager depends on the successfull run of the neighbouring geometries to export a particular job. If a large number of jobs are failed or the database doesn't have enough neighbour information the RunManager sequence can break. In that case, a new job has to be exported manully.
5. To add some new geometries to an existing data base, re-run the `CreateNewDbs.py` by providing the __new complete list of full geometries__. The script will check for existing geometries in the data base and update it with new additional geometries. This will modify all the neighbour geometry information, but won't interfere with any existing results in database.
6. If some calc is semi successful i.e. if like mrci enrgy and ddr are done in a single calc and energy is successful but nact is failed, then run the `collectFailed.py` by providing the `export.dat` as a command-line argument to store the semi successful jobs in a new table in database. This script will also store the result in datafile.





### Notes for H3 system:
1. The calculation is done in two steps/template. First is the multi which is one done sequencially/parallely for each one of the geoemtry. The other one does mrci-ddr together in one template, this is done in parallelly for multiple geometry.
2. In multi case only the concerned geometry file is created while in mrci-ddr case 4 additional geometry are also created for the ddr nact. The values of dphi/dtheta, for simplicity, __are hard coded in the geometry file and in the template__.
3. The RunManager itself parses the multi energy files, to parse and save the nact and mrci data run the readresult script.


### Steps to run for H3:
1. Modify `rho` in CreateNewDps.py (line 150) and run to create a grid of theta-phi for a fixed value of rho.
2. Run `python PESMan.py addcalc` to add the multi and mrci-ddr calculation information to the database (defined in pesman.config).
3. For first time run `python PESMan.py export -cid 1 -gid 1 -sid 0` to export 1st geometry to run the multi calulation > Run > import it with `PESMan.py import -e ....`
4. Now start RunManager script to do multi calculation for all the geometries sequentially. Be careful about the depth value in the script. __multi calculation doesn't gain much from parallel running, so just run it in single processor.__
5. Run `./PESMan.py export -cid 2 -j 1000 -n 3 -par` to parallely (3 process) export 1000, calc id 2 i.e. mrci-ddr job > Run > import as 
`PESMan.py import -e <file> -ig wfu -n 3 -zip -del`. `-ig wfu` ignores mrci-ddr wavefunction files during import as they are not necessary to save.
6. For H3 template, sometime the energy is done but the nact is failed and pesman can't import the job for that particular geometry, even though the enrgy result is available. In that case run the `collectFailed.py` script to collect such jobs for the job-run directory.
7. At the end run `./PESMan.py zip -all` to archive all data in GeomData folder, if any.