import os

import models
import logging

def main(PDBDownloadID, userInputChains):
    """Perform the download generation."""

    # Setup logging for exceptions.
    logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Establish the location of the data files containing the chain and similarity information.
        projectDirectory = os.path.dirname(os.path.realpath(__file__))
        PDBData = os.path.join(projectDirectory, 'Data')
        chainData = os.path.join(PDBData, 'Chains.tsv')
        similarityData = os.path.join(PDBData, 'Similarity')
        similarityFiles = [os.path.join(similarityData, i) for i in os.listdir(similarityData)]

        # Extract the chains the user wants.
        outputChains = []
        representativeGroupsOfInterest = set([])
        readChainData = open(chainData, 'r')
        outputChains.append(readChainData.readline())  # Add the header to the set of chains.
        for line in readChainData:
            # Parse the data file containing all the chains in the PDB, and record only those that meet the quality criteria.
            chunks = (line.strip()).split('\t')
            chain = chunks[0]
            if chain in userInputChains:
                outputChains.append(line)
                representativeGroup = chunks[6]
                representativeGroupsOfInterest.add(representativeGroup)
        readChainData.close()

        # Extract the similarities that go with the chains.
        outputSimilarities = set([])
        header = ''
        for i in similarityFiles:
            readSimilarities = open(i, 'r')
            header = readSimilarities.readline()  # Strip the header.
            for line in readSimilarities:
                chunks = (line.strip()).split('\t')
                representativeGroupA = chunks[0]
                representativeGroupB = chunks[1]
                similarity = float(chunks[2])
                addSimilarity = ((representativeGroupA in representativeGroupsOfInterest) and
                                 (representativeGroupB in representativeGroupsOfInterest)
                                )
                if addSimilarity:
                    # The sequences are of interest and too similar.
                    outputSimilarities.add(line)
            readSimilarities.close()

        # Get the user request entity and record the results.
        PDBDownload = models.PDBDownload.get_by_id(PDBDownloadID)  # The PDBDownload entity.
        PDBDownload.chains = ''.join(outputChains)
        PDBDownload.similarities = header + ''.join(outputSimilarities)
        PDBDownload.finished = True
        PDBDownload.put()
    except:
        logging.exception('PDB download {0} broke down. It contained {1} chains and {2} similarities.'.format(PDBDownloadID,
                          len(outputChains) - 1, len(outputSimilarities) - 1))

    return ''