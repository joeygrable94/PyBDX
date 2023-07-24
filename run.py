from lib.config import get_client
from lib.DataSoup import BDXDataSoup
from lib.PyBDXBuilder import PyBDX
from knockknock import slack_sender

# load Client from environment
CLIENT = get_client()

@slack_sender(
    webhook_url=CLIENT.REPORT_AUTOMATION_WEBHOOK,
    channel='report-automation',
    user_mentions=['joey@getcommunity.com']
)
def fetch_bdx_pricing():
    output_message = []
    try:
        # run PyBDX
        BDX: PyBDX = PyBDX(
            client=CLIENT, download=True, analyze=True, convert=True, upload=False
        )
        # Load current data
        cur_file = f"{BDX.xml_files.data[0].src}/{BDX.xml_files.data[0].file}"
        BDX_curr: BDXDataSoup | None = BDX.ReheatSoup(cur_file, CLIENT)
        if not isinstance(BDX_curr, BDXDataSoup):
            raise Exception('BDXDataSoup not found')
        
        # append data source info
        cur_data_source = "Current: %d plans found in %s" % (
            len(BDX_curr.raw["plans"]), cur_file
        )
        output_message.append(cur_data_source)

        # Load previous data if applicable
        BDX_prev: BDXDataSoup | None = None
        if len(BDX.xml_files.data) > 1:
            prev_file = f"{BDX.xml_files.data[0].src}/{BDX.xml_files.data[1].file}"
            BDX_prev = BDX.ReheatSoup(prev_file, CLIENT)
            if not isinstance(BDX_prev, BDXDataSoup):
                raise Exception('Previous BDXDataSoup not found')
            prev_data_source = "Previous: %d plans found in %s" % (
                len(BDX_prev.raw["plans"]), prev_file
            )
            output_message.append(prev_data_source)

        output_message.append(16 * "----")

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

            prev_plan = None
            if BDX_prev is not None:
                # previous plan, builder, and subdiv
                prev_plan = (
                    BDX.findMatchingPlan(
                        needle=cur_plan,
                        haystack=BDX_prev.raw["plans"]
                    ) or None
                )
                pp_builder = (
                    BDX.findMatchingCPT(
                        needle=prev_plan.builder,
                        haystack=BDX_prev.raw["builders"]
                    )
                    if prev_plan and len(prev_plan.builder) > 0
                    else None
                )
                pp_subdiv = (
                    BDX.findMatchingCPT(
                        needle=prev_plan.subdiv,
                        haystack=BDX_prev.raw["subdivs"]
                    )
                    if prev_plan and len(prev_plan.subdiv) > 0
                    else None
                )

            # calculate any observed pricing changes, or get current plan price
            plan_price = BDX.calcPlanPricing(prev_plan, cur_plan)

            # print current plan info
            if cp_builder is not None:
                output_message.append(cp_builder.name)
            if cp_subdiv is not None:
                output_message.append(cp_subdiv.name)
            output_message.append(cur_plan.name)
            output_message.append(plan_price)
            output_message.append('')
    except (Exception) as e:
        output_message.append('ERROR:')
        output_message.append(e)
    finally:
        output_str = '\n'.join(output_message)
        return output_str

if __name__ == '__main__':
    fetch_bdx_pricing()
