REM glpsol -m aps.mod -d aps.dat -d 31.dat --wlp aps.lp --check
REM highs --model_file .\aps.lp --options_file aps.opt 
REM glpsol -m aps.mod -d aps.dat -d 31.dat -r aps.sol

@echo off
echo Running GLPSOL to generate LP...
@REM call glpsol -m aps.mod -d aps.dat --wlp aps.lp --check
@REM call glpsol -m aps.mod -d aps.dat --cuts --scale --adv --check --wmps aps.mps --nomip
call glpsol -m aps.mod -d LS.dat -d LS_distdur.dat --cuts --scale --adv --check --wmps aps.mps --nomip

echo Running HiGHS solver...
@REM call highs --model_file .\aps.lp --options_file aps.opt
call C:\Solvers\highs --model_file .\aps.mps --options_file aps.opt 

echo Running GLPSOL again to generate solution...
@REM call glpsol -m aps.mod -d aps.dat -r aps.sol
call glpsol -m aps.mod -d LS.dat -d LS_distdur.dat -r aps.sol

echo Done.
pause
