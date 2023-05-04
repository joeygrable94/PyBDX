from lib.config import get_client
from lib.DataSoup import BDXDataSoup
from lib.PyBDXBuilder import PyBDX

# load Client from env and run PyBDX
CLIENT = get_client()
BDX: PyBDX = PyBDX(
    client=CLIENT, download=True, analyze=True, convert=True, upload=False
)

# load data sets
cur_file = f"{BDX.xml_files.data[0].src}/{BDX.xml_files.data[0].file}"
prev_file = f"{BDX.xml_files.data[0].src}/{BDX.xml_files.data[1].file}"

# rebuild datasoup
BDX_curr: BDXDataSoup | None = BDX.ReheatSoup(cur_file, CLIENT)
BDX_prev: BDXDataSoup | None = BDX.ReheatSoup(prev_file, CLIENT)

if not isinstance(BDX_curr, BDXDataSoup) or not isinstance(BDX_prev, BDXDataSoup):
    print("Error: BDXDataSoup not found")
    exit()

# print data source info
print(len(BDX_prev.raw["plans"]), "plans found in", prev_file)
print(len(BDX_curr.raw["plans"]), "plans found in", cur_file)
print(16 * "----")

# exit()
# loop current and previous plans
for i, cur_plan in enumerate(BDX_curr.raw["plans"]):
    # current plan builder and subdiv
    cp_builder = (
        BDX.findMatchingCPT(
            needle=cur_plan.builder[0], haystack=BDX_curr.raw["builders"]
        )
        if len(cur_plan.builder) > 0
        else None
    )
    cp_subdiv = (
        BDX.findMatchingCPT(needle=cur_plan.subdiv[0], haystack=BDX_curr.raw["subdivs"])
        if len(cur_plan.subdiv) > 0
        else None
    )

    # previous plan, builder, and subdiv
    prev_plan = (
        BDX.findMatchingPlan(needle=cur_plan, haystack=BDX_prev.raw["plans"]) or None
    )
    pp_builder = (
        BDX.findMatchingCPT(needle=prev_plan.builder, haystack=BDX_prev.raw["builders"])
        if prev_plan and len(prev_plan.builder) > 0
        else None
    )
    pp_subdiv = (
        BDX.findMatchingCPT(needle=prev_plan.subdiv, haystack=BDX_prev.raw["subdivs"])
        if prev_plan and len(prev_plan.subdiv) > 0
        else None
    )

    # calculate any observed pricing changes, or get current plan price
    plan_price = BDX.calcPlanPricing(prev_plan, cur_plan)

    # print current plan info
    if cp_builder is not None:
        print(cp_builder.name)
    if cp_subdiv is not None:
        print(cp_subdiv.name)
    print(cur_plan.name, "[ + ADDED ]") if prev_plan is None else print(cur_plan.name)
    # print(cur_plan.wp_cpt_id)
    print(plan_price)
    print()
