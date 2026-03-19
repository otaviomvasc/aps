@echo off
echo Running GLPSOL ...
@REM call glpsol -m aps.mod -d aps.dat --check
@REM call glpsol -m aps.mod -d aps.dat --cuts --scale --adv --mipgap 0.05
@REM call glpsol -m aps.mod -d aps.dat --cuts --scale --adv --mipgap 1.e-3 
@REM call glpsol -m aps.mod -d LS.dat -d LS_distdur.dat --check
@REM call glpsol -m aps.mod -d LS.dat -d LS_distdur.dat --mipgap 0.05 --cuts --scale --adv 
call glpsol -m aps2.mod -d aps.dat --mipgap 0.05 --cuts --scale --adv 


