from google.appengine.ext import ndb

class CullJob(ndb.Model):
	similarity = ndb.FloatProperty(required=True)
	minRes = ndb.FloatProperty(required=True)
	maxRes = ndb.FloatProperty(required=True)
	maxRVal = ndb.FloatProperty(required=True)
	minLen = ndb.IntegerProperty(required=True, default=-1)
	maxLen = ndb.IntegerProperty(required=True, default=-1)
	skipNonXRay = ndb.BooleanProperty(required=True, default=True)
	skipAlphaCarbonOnly = ndb.BooleanProperty(required=True, default=True)
	requestDate = ndb.DateTimeProperty(required=True)
	chains = ndb.TextProperty(required=True)
	nonredundant = ndb.TextProperty()
	email = ndb.StringProperty(required=True)

class Protein(ndb.Model):
	chain = ndb.StringProperty(required=True)  # Also used as the unique id for the entity.
	resolution = ndb.FloatProperty(required=True)
	rVal = ndb.FloatProperty(required=True)
	sequence = ndb.TextProperty(required=True)
	sequenceLength = ndb.ComputedProperty(lambda self: len(self.sequence))
	nonXRay = ndb.BooleanProperty(required=True)
	alphaCarbonOnly = ndb.BooleanProperty(required=True)
	similarityGroup = ndb.StringProperty(required=True)

class SimilarityGroup(ndb.Model):
	similarityGroup = ndb.StringProperty(required=True)  # Also used as the unique id for the entity.
	content = ndb.TextProperty(required=True)

class PreCulledList(ndb.Model):
	# The details are in the form A_B_C_D_E_F where
	# A is the similarity cutoff used
	# B is the maximum resolution
	# C is the maximum R value
	# D is whether nonXRay structures are skipped (Y or N)
	# E is whether alpha carbon only structures are skipped (Y or N)
	details = ndb.StringProperty(required=True)  # Also used as the unique id for the entity.
	listBlobKey = ndb.BlobKeyProperty(required=True)