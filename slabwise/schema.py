"""Data schema shared by every source adapter, the simulator and the estimators.

A *sale record* is one completed transaction as it arrives from a feed (before
the identity layer). Any real data source must be converted to this schema
(pillar P19). Columns prefixed ``t_`` exist only in simulated data: they hold
the ground truth and are never read by an estimator.
"""

GRADES = (10, 9, 8, 7)          # in-scope grades, index 0 is the reference grade
GRADE_INDEX = {g: i for i, g in enumerate(GRADES)}

# Observed columns (what a real feed can provide)
OBSERVED = [
    "sale_id",      # unique id of this record in our store
    "item_id",      # marketplace listing id (duplicates across feeds share it)
    "day",          # float, days since start of history
    "week",         # int, day // 7
    "card",         # int, catalogue card id as matched from the title
    "grade",        # int, grade as stated in title / structured field
    "cert",         # str or None, certificate number if shown
    "venue",        # "ebay" | "auction"
    "price",        # float, USD, hammer + buyer premium, excluding shipping
    "flag_lot",     # bool, title rules detected a multi-card lot
    "flag_bo",      # bool, Best Offer accepted with hidden price (price = ask)
]

# Ground-truth columns (simulation only)
TRUTH = [
    "t_kind",       # "genuine" or contamination type
    "t_card",       # real card (or -1 for an out-of-catalogue variant / fake)
    "t_grade",      # real grade
    "t_copyq",      # log quality offset of the specific copy
]

CONTAMINATION_TYPES = (
    "misgrade",     # title says a higher grade than the slab
    "raw",          # raw card sold as graded / "PSA 10 ready"
    "fake",         # counterfeit or reprint
    "variant",      # different printing (1st ed / unlimited / language)
    "lot",          # multi-card lot
    "bo_ask",       # Best Offer recorded at asking price
    "shill",        # unpaid or shill-inflated auction
    "duplicate",    # the same sale reported twice
)
