REM glpsol -m aps.mod -d aps.dat -d 31.dat --wlp aps.lp --check
REM highs --model_file .\aps.lp --options_file aps.opt 
REM glpsol -m aps.mod -d aps.dat -d 31.dat -r aps.sol

@echo off
set "DAT_FILE=C:\Users\marce\OneDrive\Área de Trabalho\aps\arquivos_dat\Lagoa_Santa.dat"
set "DIST_DAT_FILE=C:\Users\marce\OneDrive\Área de Trabalho\aps\arquivos_dat\Dist_Lagoa_Santa_distance.dat"

echo Running GLPSOL to generate LP...
@REM call glpsol -m aps.mod -d "%DAT_FILE%" --wlp aps.lp --check
@REM "C:\GLPK\glpsol.exe" -m aps.mod -d "%DAT_FILE%" --cuts --scale --adv --check --wmps aps.mps --nomip

call "C:\GLPK\glpsol.exe" -m aps.mod -d "%DAT_FILE%" -d "%DIST_DAT_FILE%" --cuts --scale --adv --check --wmps aps.mps --nomip
@REM call glpsol -m aps.mod -d LS.dat -d LS_distdur.dat --cuts --scale --adv --check --wmps aps.mps --nomip

echo Running HiGHS solver...
@REM call highs --model_file .\aps.lp --options_file aps.opt
@REM call C:\Solvers\highs --model_file .\aps.mps --options_file aps.opt 

echo Running GLPSOL again to generate solution...
call "C:\GLPK\glpsol.exe" -m aps.mod -d "%DAT_FILE%" -d "%DIST_DAT_FILE%" -r aps.sol
@REM call glpsol -m aps.mod -d LS.dat -d LS_distdur.dat -r aps.sol

echo Done.
pause
