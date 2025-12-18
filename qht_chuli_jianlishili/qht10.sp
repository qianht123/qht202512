subckt TEST4_06 Ain Bin Vout VDD GND

M4 (Vout net07 VDD VDD) pch_lvt l=40n w=120n m=1 nf=4 sd=140n ad=1.32e-14         as=1.32e-14 pd=460n ps=460n nrd=0.280589 nrs=0.280589 sa=110n         sb=110n
M1 (net07 Bin net16 VDD) pch_lvt l=40n w=120n m=1 nf=4 sd=140n ad=1.32e-14         as=1.32e-14 pd=460n ps=460n nrd=0.280589 nrs=0.280589 sa=110n         sb=110n
M0 (net16 Ain VDD VDD) pch_lvt l=40n w=120n m=1 nf=4 sd=140n ad=1.32e-14         as=1.32e-14 pd=460n ps=460n nrd=0.280589 nrs=0.280589 sa=110n         sb=110n
M5 (Vout net07 GND GND) nch_lvt l=40n w=120n m=1 nf=4 sd=140n ad=1.32e-14         as=1.32e-14 pd=460n ps=460n nrd=0.193171 nrs=0.193171 sa=110n         sb=110n
M3 (net07 Bin GND GND) nch_lvt l=40n w=120n m=1 nf=4 sd=140n ad=1.32e-14         as=1.32e-14 pd=460n ps=460n nrd=0.193171 nrs=0.193171 sa=110n         sb=110n
M2 (net07 Ain GND GND) nch_lvt l=40n w=120n m=1 nf=4 sd=140n ad=1.32e-14         as=1.32e-14 pd=460n ps=460n nrd=0.193171 nrs=0.193171 sa=110n         sb=110n


ends TEST4_06