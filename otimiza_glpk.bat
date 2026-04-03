@echo off
echo Running GLPSOL ...
@REM call glpsol -m aps.mod -d aps.dat --check
@REM call glpsol -m aps.mod -d aps.dat --cuts --scale --adv --mipgap 0.05
@REM call glpsol -m aps.mod -d aps.dat --cuts --scale --adv --mipgap 1.e-3 
@REM call glpsol -m aps.mod -d LS.dat -d LS_distdur.dat --check
@REM call glpsol -m aps.mod -d LS.dat -d LS_distdur.dat --mipgap 0.05 --cuts --scale --adv 
@REM call glpsol -m aps.mod -d LS_CLU.dat -d LS_CLU_distdur.dat --mipgap 0.05 --cuts --scale --adv 
@REM call glpsol -m aps.mod -d Cont_CLU.dat -d Cont_CLU_distdur.dat --mipgap 0.05 --cuts --scale --adv 
call glpsol -m aps.mod -d MC_CLU.dat -d MC_CLU_distdur.dat --mipgap 0.05 --cuts --scale --adv 
@REM call glpsol -m aps.mod -d Div_CLU.dat -d Div_CLU_distdur.dat --mipgap 0.05 --cuts --scale --adv 
@REM call glpsol -m aps.mod -d BH_CLU.dat -d BH_CLU_distdur.dat --mipgap 0.05 --cuts --scale --adv 

