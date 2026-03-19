@echo off
echo Running AMPL-Gurobi ...
REM call glpsol -m aps.mod -d aps.dat -d 31.dat --mipgap 0.001 --cuts
call ampl aps.run