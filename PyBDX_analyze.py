# ---------------------------------------------------------------------------
# IMPORTS
from dotenv import load_dotenv
load_dotenv()

from lib.PyBDX import PyBDX
# from lib import client_WhitneyRanch as CLIENT
from lib import client_RiverIslands as CLIENT

# run PyBDX
BDX = PyBDX(client=CLIENT,
            download= False,
            analyze = False,
            convert = False,
            upload  = False)

# load data sets
curr_file = f'{BDX.xml_files.data[0].src}/{BDX.xml_files.data[0].file}'
prev_file = f'{BDX.xml_files.data[0].src}/{BDX.xml_files.data[1].file}'

# rebuild datasoup
BDX_curr = BDX.ReheatSoup(curr_file, CLIENT)
BDX_prev = BDX.ReheatSoup(prev_file, CLIENT)

# print data source info
print(len(BDX_prev.raw['plans']), 'plans found in', prev_file)
print(len(BDX_curr.raw['plans']), 'plans found in', curr_file)
print(17*'-----')

# exit()
# loop current and previous plans
for i, curr_plan in enumerate(BDX_curr.raw['plans']):

    # current plan builder and subdiv
    cp_builder = BDX.findMatchingCPT(needle=curr_plan.builder[0], haystack=BDX_curr.raw['builders']) if len(curr_plan.builder) > 0 else None
    cp_subdiv = BDX.findMatchingCPT(needle=curr_plan.subdiv[0], haystack=BDX_curr.raw['subdivs']) if len(curr_plan.subdiv) > 0 else None

    # previous plan, builder, and subdiv
    prev_plan = BDX.findMatchingPlan(needle=curr_plan, haystack=BDX_prev.raw['plans']) or None
    pp_builder = BDX.findMatchingCPT(needle=prev_plan.builder, haystack=BDX_prev.raw['builders']) if prev_plan and len(prev_plan.builder) > 0 else None
    pp_subdiv = BDX.findMatchingCPT(needle=prev_plan.subdiv, haystack=BDX_prev.raw['subdivs']) if prev_plan and len(prev_plan.subdiv) > 0 else None

    # calculate any observed pricing changes, or get current plan price
    plan_price = BDX.calcPlanPricing(prev_plan, curr_plan)
    print('----'*10)

    # current Plan Builder
    if cp_builder is not None:
        print(cp_builder.name)

    # current Plan Sub Division
    if cp_subdiv is not None:
        print(cp_subdiv.name)

    # current Plan
    print(curr_plan.name)

    # current Plan Price
    if plan_price is not None:
        print(plan_price)

    # current Plan images
    if len(curr_plan._images):
        print('IMG:')
        for img in curr_plan._images:
            if img.get('slug'):
                print(img.get('slug'))
            if img.get('title'):
                print(img.get('title'))
            if img.get('caption'):
                print(img.get('caption'))
    if len(curr_plan._floorplans):
        print('FLOORPLANS:')
        for img in curr_plan._floorplans:
            if img.get('slug'):
                print(img.get('slug'))
            if img.get('title'):
                print(img.get('title'))
            if img.get('caption'):
                print(img.get('caption'))
    if len(curr_plan._interiors):
        print('INTERIORS:')
        for img in curr_plan._interiors:
            if img.get('slug'):
                print(img.get('slug'))
            if img.get('title'):
                print(img.get('title'))
            if img.get('caption'):
                print(img.get('caption'))
    if len(curr_plan._elevations):
        print('ELEVATIONS:')
        for img in curr_plan._elevations:
            if img.get('slug'):
                print(img.get('slug'))
            if img.get('title'):
                print(img.get('title'))
            if img.get('caption'):
                print(img.get('caption'))

    # Download Images
    # BDX.downloadImages(obj=curr_plan, kind='floorplans')
    # BDX.downloadImages(obj=curr_plan, kind='elevations')
    # BDX.downloadImages(obj=curr_plan, kind='images')
    # BDX.downloadImages(obj=curr_plan, kind='interiors')
