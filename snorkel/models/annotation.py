from .meta import SnorkelBase, snorkel_postgres
from sqlalchemy import Column, String, Integer, Float, ForeignKey, UniqueConstraint, Table, PickleType
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects import postgresql
from snorkel.utils import camel_to_under


class AnnotationKey(SnorkelBase):
    """
    The Annotation key table is a mapping from unique string names to integer id numbers.
    These strings uniquely identify who or what produced an annotation.
    """
    __tablename__ = 'annotation_key'
    id        = Column(Integer, primary_key=True)
    name      = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return str(self.__class__.__name__) + " (" + str(self.name) + ")"


# TODO: Make this whole thing polymorphic instead now that only one AnnotationKey class?
class AnnotationMixin(object):
    """
    Mixin class for defining annotation tables.

    An annotation is a value associated with a Candidate. Examples include labels, features,
    and predictions.

    New types of annotations can be defined by creating an annotation class and corresponding annotation, for example:

    .. code-block:: python

        from snorkel.models.annotation import AnnotationMixin
        from snorkel.models.meta import SnorkelBase

        class NewAnnotation(AnnotationMixin, SnorkelBase):
            value = Column(Float, nullable=False)


        # The entire storage schema, including NewAnnotation, can now be initialized with the following import
        import snorkel.models

    The annotation class should include a Column attribute named value.
    """
    @declared_attr
    def __tablename__(cls):
        return camel_to_under(cls.__name__)

    # The key is the "name" or "type" of the Annotation- e.g. the name of a feature, or of a human annotator
    @declared_attr
    def key_id(cls):
        return Column('key_id', Integer, ForeignKey('annotation_key.id'), primary_key=True)

    @declared_attr
    def key(cls):
        return relationship('AnnotationKey', backref=backref(camel_to_under(cls.__name__) + 's', cascade='all, delete-orphan'))

    # Every annotation is with respect to a candidate
    @declared_attr
    def candidate_id(cls):
        return Column('candidate_id', Integer, ForeignKey('candidate.id'), primary_key=True)

    @declared_attr
    def candidate(cls):
        return relationship('Candidate', backref=backref(camel_to_under(cls.__name__) + 's', cascade='all, delete-orphan', cascade_backrefs=False),
                            cascade_backrefs=False)

    # NOTE: What remains to be defined in the subclass is the **value**

    def __repr__(self):
        return self.__class__.__name__ + " (" + str(self.key.name) + " = " + str(self.value) + ")"


class Label(AnnotationMixin, SnorkelBase):
    """
    A discrete label associated with a Candidate, indicating a target prediction value.

    Labels are used to represent both human-provided annotations and the output of labeling functions.

    A Label's annotation key identifies the person or labeling function that provided the Label.
    """
    value = Column(Integer, nullable=False)


class Feature(AnnotationMixin, SnorkelBase):
    """
    An element of a representation of a Candidate in a feature space.

    A Feature's annotation key identifies the definition of the Feature, e.g., a function that implements it
    or the library name and feature name in an automatic featurization library.
    """
    value = Column(Float, nullable=False)


class Prediction(AnnotationMixin, SnorkelBase):
    """
    A probability associated with a Candidate, indicating the degree of belief that the Candidate is true.

    A Prediction's annotation key indicates which process or method produced the Prediction, e.g., which
    model with which ParameterSet.
    """
    value = Column(Float, nullable=False)


class StableLabel(SnorkelBase):
    """
    A special secondary table for preserving labels created by *human annotators* (e.g. in the Viewer)
    in a stable format that does not cascade, and is independent of the Candidate ids.
    """
    __tablename__  = 'stable_label'
    context_stable_ids = Column(String, primary_key=True)  # ~~ delimited list
    annotator_name     = Column(String, primary_key=True)
    split              = Column(Integer, default=0)
    value              = Column(Integer, nullable=False)

    def __repr__(self):
        return "%s (%s : %s)" % (self.__class__.__name__, self.annotator_name, self.value)
