#!/bin/bash
# shell script td  short scan and plot the spectrum of
# a scan on the mark6 recorder.

startfreq=0   # start baseband frequency in MHz
stopfreq=2048   # stop  baseband frequency in MHz

                                                              
basedir=/home/oper

[ -d $basedir/linecheck ] || mkdir $basedir/linecheck
[ -d $basedir/linecheck ] || { echo "ERROR: Could not create directory: $basedir/linecheck"; exit 1; }

now=$(date +"%Y-%m-%d-%H-%M-%S")
workdir=$basedir/linecheck/$now
#datafile=$basedir/linecheck/$now/data_$now.m5b

mkdir $workdir
[ -d $workdir ] || { echo "ERROR: Could not create directory: $workdir"; exit 1; }

cd $workdir

# record a 10 second scan
da-client <<EOF
mstat?all
record=on:10:10:$now:tone:pv
quit
EOF

# fuse mount the module
sleep 5
fusermount -u /mnt/diskpack/stream1
fusermount -u /mnt/diskpack/stream2
vdifuse -a tone12.cache -xm6sg /mnt/diskpack/stream1 /mnt/disks/[12]/?/data
vdifuse -a tone34.cache -xm6sg /mnt/diskpack/stream2 /mnt/disks/[34]/?/data

# run m5spec for LCP and RCP 
/usr/local/src/difx/bin/m5spec /mnt/diskpack/stream1/sequences/tone/pv/$now.vdif VDIF_8192-8000-1-2 2048 100 data12.m5spec
/usr/local/src/difx/bin/m5spec /mnt/diskpack/stream2/sequences/tone/pv/$now.vdif VDIF_8192-8000-1-2 2048 100 data34.m5spec

# unmount fuse
fusermount -u /mnt/diskpack/stream1
fusermount -u /mnt/diskpack/stream2

# generate gnuplot config file
outfile=data.gnu
echo "set term 'wxt'" > $outfile
echo "set multiplot layout 2,1 title 'R2DBE: $now'" >> $outfile
echo "set style data line" >> $outfile
echo "set grid x" >> $outfile
echo "set xtics 0,256" >> $outfile

echo "set xlabel 'frequency [MHz]'" >> $outfile
echo "set ylabel 'amplitude'">> $outfile
echo "unset key" >> $outfile
echo "set title 'Pol 0'" >> $outfile
#echo "set term 'png'"  >> $outfile
#echo "set out 'data.png'"  >> $outfile
echo "plot 'data12.m5spec' u 1:2 w l" >> $outfile
echo "set title 'Pol 1'" >> $outfile
echo "plot 'data34.m5spec' u 1:2 w l" >> $outfile
#echo "replot"  >> $outfile
echo "unset multiplot" >> $outfile

gnuplot --persist data.gnu

