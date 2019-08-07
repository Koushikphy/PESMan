***,HeH2+
! multimrci1-geom589-1 : basename to be substituted
file,2,multimrci1-geom589-1.wfu
punch,multimrci1-geom589-1.pun

basis=cc-pvtz;

symmetry,nosym
orient,noorient
geometry=multimrci1-geom589-1.xyz

{mcscf;
occ,10;closed,0;
wf,3,1,1;state,2;
maxiter,40;
start,2341.2;
orbital,2341.2;}

{mcscf;
occ,10;closed,0;
wf,3,1,1;state,3;
maxiter,40;
start,2341.2;
orbital,2342.2;}


show,energy
table,energy
save,multimrci1-geom589-1.res,new
title 'Multi-results: Energies ---  multimrci1-geom589-1'

{ci;occ,10;core,0;closed,0;maxiter,200,200;
 wf,3,1,1;state,3;}


show,energy
table,energy
save,multimrci1-geom589-1.res,new
title 'Mrci-results: Energies ---  multimrci1-geom589-1'

