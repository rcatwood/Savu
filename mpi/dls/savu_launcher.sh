#!/bin/bash -x
module load global/cluster

echo "SAVU_LAUNCHER:: Running Job"

savupath=$SAVUHOME
datafile=$1
processfile=$2
outpath=$3
outname=savu
nNodes=1
nCPUs=12
evars="SAVUHOME=$SAVUHOME PYTHONPATH=$PYTHONPATH "

datestring=`date +%Y_%m%d_%H%M%S`

msgpath=$outpath/${datestring}_savufiles

if [[ -e $msgpath ]]
then
   echo "WARNING: $msgpath already exists!"
   echo "using anyways..."
fi

mkdir -p $msgpath

if [[ ! -d $msgpath ]]
then
   echo "ERROR: $msgpath could not be created properly .. is not a directory"
   exit
fi

filepath=$savupath/mpi/dls/savu_mpijob.sh
M=$((nNodes*12))

qsub -N $outname -v SAVUHOME -v PYTHONPATH -v DATESTRING=$datestring -o $msgpath -e $msgpath -pe openmpi $M -l exclusive -l infiniband -q medium.q@@com10 $filepath $savupath $datafile $processfile $outpath $nCPUs > $msgpath/$USER.out

echo "SAVU_LAUNCHER:: Job launched on the cluster..."

filename=`echo $outname.o`
jobnumber=`awk '{print $3}' $msgpath/$USER.out | head -n 1`
filename=$msgpath/$filename$jobnumber
echo "Job number is $jobnumber. Message files are in $msgpath "
echo "$filename"



