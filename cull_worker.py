from datetime import datetime
import os

from main import app
import models
import logging

import leafcull

def main(cullJobID, representativeGroupings, sequenceIdentity):
    """Perform the culling."""

    # Setup logging for exceptions.
    logging.getLogger().setLevel(logging.DEBUG)

    # Initialise notification variables for access in the except statements.
    numberSimmilarities = 0

    try:
        # Establish the location of the data files containing the similarity information.
        projectDirectory = os.path.dirname(os.path.realpath(__file__))
        similarityData = os.path.join(projectDirectory, 'Data')
        similarityData = os.path.join(similarityData, 'Similarity')
        similarityFiles = [os.path.join(similarityData, i) for i in os.listdir(similarityData)]

        # Get the user request entity.
        cullJob = models.CullJob.get_by_id(cullJobID)  # The CullJob entity.

        # Record that the culling has started.
        cullJob.startDate = datetime.utcnow()

        # Determine the adjacency matrix.
        adjList = {}
        for i in similarityFiles:
            readSimilarities = open(i, 'r')
            readSimilarities.readline()  # Strip the header.
            for line in readSimilarities:
                chunks = (line.strip()).split('\t')
                representativeGroupA = chunks[0]
                representativeGroupB = chunks[1]
                similarity = float(chunks[2])
                addSimilarity = ((representativeGroupA in representativeGroupings) and
                                 (representativeGroupB in representativeGroupings) and
                                 (similarity >= sequenceIdentity)
                                )
                if addSimilarity:
                    # The sequences are of interest and too similar.
                    chainA = representativeGroupings[representativeGroupA]
                    chainB = representativeGroupings[representativeGroupB]
                    if chainA in adjList:
                        adjList[chainA].add(chainB)
                    else:
                        adjList[chainA] = set([chainB])
                    if chainB in adjList:
                        adjList[chainB].add(chainA)
                    else:
                        adjList[chainB] = set([chainA])
                    numberSimmilarities += 1
            readSimilarities.close()
        numberSimmilarities = str(numberSimmilarities) + ' (total)'

        # Perform culling.
        removedChains = leafcull.main(adjList)

        # Record the results.
        cullJob.nonredundant = '\n'.join([i for i in representativeGroupings.values() if not i in removedChains])
        cullJob.finished = True
        cullJob.put()
    except:
        logging.exception('CullJob {0} broke down. It contained {1} uniqe chains and {2} similarities.'.format(cullJobID,
                          len(representativeGroupings), numberSimmilarities))

    return ''