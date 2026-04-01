from __future__ import annotations

from dataclasses import dataclass

from contracts.intent_schema import (
    ActivityLocationContext,
    ActivityProfile,
    ActivityType,
    ExpectedDurationBand,
    ExposureLevel,
    IntensityLevel,
    MotionPattern,
)


@dataclass(frozen=True)
class ActivityOntologyEntry:
    activity: ActivityType
    variants: tuple[str, ...]
    profile: ActivityProfile


ACTIVITY_ONTOLOGY: tuple[ActivityOntologyEntry, ...] = (
    ActivityOntologyEntry(
        activity=ActivityType.HIIT,
        variants=("hiit", "crossfit", "hill sprints", "sprint workout", "bootcamp"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.HIGH,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.CONTINUOUS,
            typical_duration_min=30,
            hard_upper_duration_min=180,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.RUNNING,
        variants=("run", "running", "jog", "jogging", "marathon", "10k", "5k"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.HIGH,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.CONTINUOUS,
            typical_duration_min=60,
            hard_upper_duration_min=240,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.WALKING,
        variants=("walk", "walking", "stroll", "strolling"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.MODERATE,
            motion_pattern=MotionPattern.CONTINUOUS,
            typical_duration_min=45,
            hard_upper_duration_min=240,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.CYCLING,
        variants=("cycle", "cycling", "bike", "biking", "rollerblading"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.HIGH,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.CONTINUOUS,
            typical_duration_min=60,
            hard_upper_duration_min=300,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.SOCCER,
        variants=("soccer", "football match"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.HIGH,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.INTERMITTENT,
            typical_duration_min=90,
            hard_upper_duration_min=240,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.BASKETBALL,
        variants=("basketball", "shoot hoops"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.HIGH,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.INTERMITTENT,
            typical_duration_min=90,
            hard_upper_duration_min=240,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.HIKING,
        variants=("hike", "hiking", "trail", "trek", "trekking", "treck", "trecking"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.MODERATE,
            expected_duration_band=ExpectedDurationBand.LONG,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.CONTINUOUS,
            typical_duration_min=180,
            hard_upper_duration_min=480,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.YARD_WORK,
        variants=("yard work", "lawn", "gardening", "raking", "mowing"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.MODERATE,
            expected_duration_band=ExpectedDurationBand.LONG,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.INTERMITTENT,
            typical_duration_min=120,
            hard_upper_duration_min=360,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.PARK_VISIT,
        variants=("park", "play outside", "kids to the park", "playground"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.MODERATE,
            motion_pattern=MotionPattern.INTERMITTENT,
            typical_duration_min=90,
            hard_upper_duration_min=300,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.BEACH_DAY,
        variants=("beach", "sunbathing", "beach day"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.LONG,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.STATIONARY,
            typical_duration_min=180,
            hard_upper_duration_min=480,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.FESTIVAL,
        variants=("festival", "concert", "street fair", "outdoor event"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.LONG,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.INTERMITTENT,
            typical_duration_min=240,
            hard_upper_duration_min=720,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.SIGHTSEEING,
        variants=("sightseeing", "touring", "walking tour"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.LONG,
            exposure_level=ExposureLevel.MODERATE,
            motion_pattern=MotionPattern.CONTINUOUS,
            typical_duration_min=180,
            hard_upper_duration_min=480,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.BIKE_COMMUTE,
        variants=("bike to work", "cycle to work", "jog to work", "scooter to work"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.MODERATE,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.HIGH,
            motion_pattern=MotionPattern.CONTINUOUS,
            typical_duration_min=45,
            hard_upper_duration_min=180,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.COMMUTE,
        variants=("commute", "to work", "rush hour", "route to work"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.MODERATE,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.MODERATE,
            motion_pattern=MotionPattern.CONTINUOUS,
            typical_duration_min=45,
            hard_upper_duration_min=180,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.DOG_WALK,
        variants=("dog walk", "walk my dog"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.SHORT,
            exposure_level=ExposureLevel.MODERATE,
            motion_pattern=MotionPattern.CONTINUOUS,
            typical_duration_min=20,
            hard_upper_duration_min=120,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.OUTDOOR_ERRAND,
        variants=("errand", "pickup", "grab coffee", "grocery", "mailbox", "uber", "grocery run"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.SHORT,
            exposure_level=ExposureLevel.LOW,
            motion_pattern=MotionPattern.INTERMITTENT,
            typical_duration_min=20,
            hard_upper_duration_min=120,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.BARBECUE,
        variants=("barbecue", "barbeque", "bbq", "cookout", "grill out"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.LONG,
            exposure_level=ExposureLevel.MODERATE,
            motion_pattern=MotionPattern.STATIONARY,
            typical_duration_min=180,
            hard_upper_duration_min=540,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.OUTDOOR_GATHERING,
        variants=("picnic", "patio", "outdoor dinner", "garden party", "outdoor wedding", "wedding"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.LONG,
            exposure_level=ExposureLevel.MODERATE,
            motion_pattern=MotionPattern.STATIONARY,
            typical_duration_min=240,
            hard_upper_duration_min=720,
        ),
    ),
    ActivityOntologyEntry(
        activity=ActivityType.OPEN_WINDOWS,
        variants=("open windows", "open the windows", "open window"),
        profile=ActivityProfile(
            exertion_level=IntensityLevel.LOW,
            expected_duration_band=ExpectedDurationBand.MEDIUM,
            exposure_level=ExposureLevel.LOW,
            location_context=ActivityLocationContext.INDOOR_OUTDOOR_BOUNDARY,
            motion_pattern=MotionPattern.STATIONARY,
            typical_duration_min=60,
            hard_upper_duration_min=720,
        ),
    ),
)


@dataclass
class ActivityNormalizer:
    def normalize(self, message: str) -> tuple[ActivityType, ActivityProfile | None]:
        lowered = message.lower()
        for entry in ACTIVITY_ONTOLOGY:
            if any(variant in lowered for variant in entry.variants):
                return entry.activity, entry.profile.model_copy(deep=True)
        return ActivityType.UNKNOWN, None
