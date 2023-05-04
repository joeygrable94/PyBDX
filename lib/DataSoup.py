import math
from datetime import datetime
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from lib import constants as C, utilities as UT


# ----------------------------------------------------------------------------------------
# NODE base data class
class Node:
    def __repr__(self) -> str:
        """representation"""
        return '<Node BDX id="%s">' % (self.id)

    def __init__(self, id: Any, number: Any, name: Any) -> None:
        """constructor"""
        self.id = id
        self.number = number
        self.name = name

    def getDataTag(self, data: Any, tag_name: Any) -> Any:
        """find tag name and return its contents"""
        tag_data = data.find(tag_name)
        if tag_data is not None:
            value = tag_data.text.strip()
            return value.replace("\n", "<br>")

    def getDataBool(self, data: Any, tag_name: Any) -> Any:
        return 1 if data.find(tag_name).text.strip() == 0 else 0


# ----------------------------------------------------------------------------------------
# COMPANY data class
class Company(Node):
    def __repr__(self) -> str:
        """representation"""
        return "<Company %s>" % (self.name)

    def __init__(self, data: Any) -> None:
        """constructor"""
        Node.__init__(
            self,
            data.attrs["CorporationID"],
            data.find("CorporateBuilderNumber").text.strip(),
            data.find("CorporateName").text.strip(),
        )

    def getDict(self) -> Dict[str, Any]:
        """as dict"""
        return UT.getDict(self)


# ----------------------------------------------------------------------------------------
# BUILDER data class
class Builder(Node):
    def __repr__(self) -> str:
        """representation"""
        return "<Builder %s (%s)>" % (self.name, self.wp_cpt_id)

    def __init__(self, data: Any, company: Any, clientSlugs: Any) -> None:
        """constructor"""
        # relationships
        self.subdivs: List = []
        self.plans: List = []
        # data attrs
        Node.__init__(
            self,
            data.attrs["BuilderID"],
            data.find("BuilderNumber").text.strip(),
            data.find("BrandName").text.strip(),
        )
        self.slug = UT.slugify("%s %s" % (self.id, self.name))
        self.wp_cpt_id = UT.BDXgetMatchingWPID(self.slug, clientSlugs)
        self.corp_id = company.id
        self.corp_name = company.name
        self.corp_number = company.number
        self.site = Node.getDataTag(self, data, "BuilderWebsite")
        self.leads_email = Node.getDataTag(self, data, "DefaultLeadsEmail")
        self.logo_md = Node.getDataTag(self, data, "BrandLogo_Med")
        self.logo_sm = Node.getDataTag(self, data, "BrandLogo_Sm")
        self.reporting_name = Node.getDataTag(self, data, "ReportingName")
        self.copy_leads_email = Node.getDataTag(self, data, "CopyLeadsEmail")

    def addRelationship(self, key: Any, value: Any) -> bool:
        """add relationship"""
        if value != -1:
            add_to = getattr(self, key)
            add_to.append(value)
            setattr(self, key, add_to)
            return True
        return False

    def getDict(self) -> Dict[str, Any]:
        """as dict"""
        return UT.getDict(self)


# ----------------------------------------------------------------------------------------
# SUBDIVISION data class
class Subdivision(Node):
    def __repr__(self) -> str:
        """representation"""
        return "<Subdivision %s (%s)>" % (self.name, self.wp_cpt_id)

    def __init__(
        self, data: Any, company: Any, builder: Any, clientSlugs: Any, filterList: Any
    ) -> None:
        """constructor"""
        # relationships
        self.builder: List = []
        self.plans: List = []
        # data attrs
        Node.__init__(
            self,
            data.attrs["SubdivisionID"],
            data.find("SubdivisionNumber").text.strip(),
            data.find("SubdivisionName").text.strip(),
        )
        self.name = UT.filterName(filterList, self.name)
        self.slug = UT.slugify("%s %s" % (self.id, self.name))
        self.wp_cpt_id = UT.BDXgetMatchingWPID(self.slug, clientSlugs)
        self.status = data.attrs["Status"]
        self.style = Node.getDataTag(self, data, "CommunityStyle") or " "
        self.link_site = Node.getDataTag(self, data, "SubWebsite") or " "
        self.link_design_center = (
            Node.getDataTag(self, data, "EnvisionDesignCenter") or " "
        )
        self.link_video_tour = Node.getDataTag(self, data, "SubVideoTour") or " "
        self.price_low = data.attrs["PriceLow"]
        self.price_high = data.attrs["PriceHigh"]
        self.size_low = data.attrs["SqftLow"]
        self.size_high = data.attrs["SqftHigh"]
        self.directions = Node.getDataTag(self, data, "DrivingDirections") or " "
        self.description = Node.getDataTag(self, data, "SubDescription") or " "
        self.headline = Node.getDataTag(
            self, data, "MarketingHeadline"
        ) or "Welcome to %s" % (self.name)
        self.leads_email = Node.getDataTag(self, data, "SubLeadsEmail")
        if "" != self.leads_email:
            self.leads_email = builder.leads_email
        self.formatAddress(data)
        self.formatOffice(data)
        self.formatSchools(data)
        self._images = self.formatSubdivImages(data, builder) or " "

    def formatAddress(self, data: Any) -> None:
        """format subdiv address"""
        address = data.findChildren("SubAddress", recursive=False)
        for elm in address:
            street = Node.getDataTag(self, data, "SubStreet1")
            county = Node.getDataTag(self, data, "SubCounty")
            city = Node.getDataTag(self, data, "SubCity")
            state = Node.getDataTag(self, data, "SubState")
            zipcode = Node.getDataTag(self, data, "SubZIP")
            Node.getDataTag(self, data, "SubCountry")
            geocode = elm.findChildren("SubGeocode")
            geoloc = []
            for coord in geocode:
                geoloc.append(Node.getDataTag(self, coord, "SubLatitude"))
                geoloc.append(Node.getDataTag(self, coord, "SubLongitude"))
        # set the Subdiv geotag
        if len(geoloc) > 0:
            self.geotag = ", ".join(geoloc)
        else:
            self.geotag = C.DEFUALT_GEOTAG
        # set the Subdiv address
        if type(street) is str:
            self.address = "%s, %s %s, %s" % (street, city, state, zipcode)
        else:
            self.address = "%s, %s %s, %s" % (county, city, state, zipcode)

    def formatOffice(self, data: Any) -> None:
        """format office data"""
        office_data = data.findChildren("SalesOffice", recursive=False)
        for office in office_data:
            sales_agents = office.findChildren("Agent")
            sales_hours = office.find("Hours")
            phone_raw = office.findChildren("Phone")
            address = office.findChildren("Address")
            for elm in address:
                street = Node.getDataTag(self, data, "Street1")
                county = Node.getDataTag(self, data, "County")
                city = Node.getDataTag(self, data, "City")
                state = Node.getDataTag(self, data, "State")
                zipcode = Node.getDataTag(self, data, "ZIP")
                Node.getDataTag(self, data, "Country")
                geocode = elm.findChildren("Geocode")
                geoloc = []
                for coord in geocode:
                    geoloc.append(Node.getDataTag(self, coord, "Latitude"))
                    geoloc.append(Node.getDataTag(self, coord, "Longitude"))
            # set the office geotag
            # set the office geotag
            if len(geoloc) > 0:
                self.office_geotag = ", ".join(geoloc)
            else:
                self.office_geotag = C.DEFUALT_GEOTAG

            # set the office address
            if type(street) is str:
                self.office_address = "%s, %s %s, %s" % (street, city, state, zipcode)
            else:
                self.office_address = "%s, %s %s, %s" % (county, city, state, zipcode)
            # set sales office hours
            if sales_hours:
                self.office_hours = sales_hours.text.strip().replace(";", ". ")
            else:
                self.office_hours = "Contact us for our location hours."
            # format agent list
            tmp_agents = []
            if sales_agents:
                for agent in sales_agents:
                    tmp_agent = agent.text.strip().split(" & ")
                    for name in tmp_agent:
                        tmp_agents.append(name)
            else:
                tmp_agents.append("")
            self.agents = ", ".join(tmp_agents)
            # format phone number
            self.office_phone = ""
            if phone_raw:
                for itm in phone_raw:
                    c_area = Node.getDataTag(self, itm, "AreaCode")
                    c_pre = Node.getDataTag(self, itm, "Prefix")
                    c_suf = Node.getDataTag(self, itm, "Suffix")
                self.office_phone = "%s-%s-%s" % (c_area, c_pre, c_suf)

    def formatSchools(self, data: Any) -> None:
        """format school data"""
        school_data = data.findChildren("Schools", recursive=False)
        self.schools = []
        # loop school district locations
        if len(school_data) > 0:
            for school in school_data:
                data_obj = {}
                district = (
                    school.find("DistrictName").text.strip()
                    if not school.find("DistrictName") is None
                    else ""
                )
                elementary = school.findChildren("Elementary")
                middle = school.findChildren("Middle")
                high = school.findChildren("High")
                data_obj["district"] = district
                data_obj["schools"] = []
                if len(elementary) > 0:
                    for elm in elementary:
                        school_name = {"school_name": elm.text.strip()}
                        if school_name not in data_obj["schools"]:
                            data_obj["schools"].append(school_name)
                if len(middle) > 0:
                    for msch in middle:
                        school_name = {"school_name": msch.text.strip()}
                        if school_name not in data_obj["schools"]:
                            data_obj["schools"].append(school_name)
                if len(high) > 0:
                    for hsch in middle:
                        school_name = {"school_name": hsch.text.strip()}
                        if school_name not in data_obj["schools"]:
                            data_obj["schools"].append(school_name)
                # add this school disctrict to the list
                self.schools.append(data_obj)
        else:
            self.schools.append({})

    def formatSubdivImages(self, data: Any, builder: Any) -> List[Any]:
        """formate subdiv images"""
        data_pile = data.findChildren("SubImage")
        return UT.formatImageData("subdiv", self.slug, data_pile)

    def addRelationship(self, key: Any, value: Any) -> bool:
        """add relationship"""
        if value != -1:
            add_to = getattr(self, key)
            add_to.append(value)
            setattr(self, key, add_to)
            return True
        return False

    def getDict(self) -> Dict[str, Any]:
        """as dict"""
        return UT.getDict(self)


# ----------------------------------------------------------------------------------------
# PLAN data class
class Plan(Node):
    def __repr__(self) -> str:
        """representation"""
        return "<Plan %s (%s)>" % (self.name, self.wp_cpt_id)

    def __init__(
        self,
        data: Any,
        company: Any,
        builder: Any,
        subdiv: Any,
        clientSlugs: Any,
        filterList: Any,
    ) -> None:
        """constructor"""
        # relationships
        self.builder: List = []
        self.subdiv: List = []
        # data attrs
        Node.__init__(
            self,
            data.attrs["PlanID"],
            data.find("PlanNumber").text.strip(),
            data.find("PlanName").text.strip(),
        )
        self.name = UT.filterName(filterList, self.name)
        self.slug = UT.slugify("%s %s" % (self.id, self.name))
        self.wp_slug = "-".join(f"{subdiv.name}-{self.name}".split(" ")).lower()
        self.wp_cpt_id = UT.BDXgetMatchingWPID(self.wp_slug, clientSlugs)
        self.headline = Node.getDataTag(
            self, data, "MarketingHeadline"
        ) or "Welcome to %s" % (self.name)
        self.description = Node.getDataTag(self, data, "Description") or " "
        self.available = not Node.getDataBool(self, data, "PlanNotAvailable")
        self.actual_price = str(round(float(Node.getDataTag(self, data, "BasePrice"))))
        self.base_price = str(
            int(math.floor(int(self.actual_price) / 100000.0)) * 100000
        )
        self.base_sqft = Node.getDataTag(self, data, "BaseSqft")
        self.link_site = Node.getDataTag(self, data, "PlanWebsite") or " "
        self.link_nhs = Node.getDataTag(self, data, "NHSPlanWebsite") or " "
        self.link_model_tour = Node.getDataTag(self, data, "VirtualTour") or " "
        self.link_design_center = (
            Node.getDataTag(self, data, "EnvisionDesignCenter") or " "
        )
        self.num_stories = Node.getDataTag(self, data, "Stories")
        num_full_baths = Node.getDataTag(self, data, "Baths")
        num_half_baths = Node.getDataTag(self, data, "HalfBaths") or 0
        self.num_baths = str(int(num_full_baths) + (int(num_half_baths) / 2)).replace(
            ".0", ""
        )
        self.num_bedrooms = Node.getDataTag(self, data, "Bedrooms")
        self.num_car_garage = Node.getDataTag(self, data, "Garage")
        self.num_dining_areas = Node.getDataTag(self, data, "DiningAreas")
        self.has_basement = Node.getDataBool(self, data, "Basement")
        living_areas = self.formatLivingAreas(data)
        self.num_living_areas = UT.sumDictKeyValues(living_areas)
        amenities = self.formatAmenities(data)
        self.num_amenities = UT.sumDictKeyValues(amenities)
        self._images = self.formatPlanImages(data)
        self.leads_phone = subdiv.office_phone
        self.leads_email = subdiv.leads_email
        self.hours = subdiv.office_hours
        self.address = subdiv.address
        self.featured_image = self.getFeaturedImage()

    def formatLivingAreas(self, data: Any) -> Dict[str, Any]:
        """format plan living areas"""
        all_spaces: Dict[str, Any] = {}
        areas = data.findChildren("LivingArea")
        for space in areas:
            s_type = space.attrs["Type"] if space.attrs.get("Type") else ""
            space.name
            s_val = space.text
            all_spaces[s_type] = (
                all_spaces[s_type] + 1 if all_spaces.get(s_type) else int(s_val)
            )
        return all_spaces

    def formatAmenities(self, data: Any) -> Dict[str, Any]:
        """format plan amenities"""
        all_feat: Dict[str, Any] = {}
        amenities = data.findChildren("PlanAmenity")
        for feature in amenities:
            a_type = feature.attrs["Type"] if feature.attrs.get("Type") else ""
            feature.name
            a_val = feature.text
            all_feat[a_type] = (
                all_feat[a_type] + 1 if all_feat.get(a_type) else int(a_val)
            )
        return all_feat

    def formatPlanImages(self, data: Any) -> Any:
        """format plan images"""
        self._elevations: List[Any] = []
        self._floorplans: List[Any] = []
        self._interiors: List[Any] = []
        all_images = data.findChildren("PlanImages")
        for img in all_images:
            elv_img_data = img.findChildren("ElevationImage")
            fp_img_data = img.findChildren("FloorPlanImage")
            int_img_data = img.findChildren("InteriorImage")
            self._elevations = UT.formatImageData("elevation", self.slug, elv_img_data)
            self._floorplans = UT.formatImageData("floorplan", self.slug, fp_img_data)
            self._interiors = UT.formatImageData("interior", self.slug, int_img_data)
        return [*self._elevations, *self._floorplans, *self._interiors]

    def getFeaturedImage(self) -> str:
        """format featured image"""
        # determined by the first elevation image in BDX plan image data
        if bool(self._elevations[0].keys()):
            if 0 < len(str(self._elevations[0]["src"])):
                return str(self._elevations[0]["src"])
        return str(" ")

    def addRelationship(self, key: Any, value: Any) -> bool:
        """add relationship"""
        if value != -1:
            add_to = getattr(self, key)
            add_to.append(value)
            setattr(self, key, add_to)
            return True
        return False

    def getDict(self) -> Dict[str, Any]:
        """as dict"""
        return UT.getDict(self)


# ----------------------------------------------------------------------------------------
# BDX data wrangler
class BDXDataSoup:
    def __repr__(self) -> str:
        """representation"""
        return "<DataSoup %s (%s) compiled: %s>" % (
            self.client.CLIENT_NAME,
            self.cid,
            self.date,
        )

    def __init__(self, data_file: Any, client: Any) -> None:
        """constructor"""
        self.raw: Dict[str, Any] = {"builders": [], "subdivs": [], "plans": []}
        self.json: Dict[str, Any] = {"builders": [], "subdivs": [], "plans": []}
        self.client: Any = client
        self.file_name: str = data_file.split("/")[-1]
        self.cid: str = ""
        self.date: Any
        file = self.file_name.split(".")[:-1][0].split("-")
        datestr = "/".join(file[1:])
        if datestr != "current":
            self.cid = file[0]
            self.date = datetime.strptime(datestr, "%Y/%m/%d")
        else:
            self.cid = file[0]
            self.date = datetime.now().strftime("%Y/%m/%d")
        # open the xml data file
        with open(data_file, "r") as raw_xml:
            content = "".join(raw_xml.readlines()).encode("UTF-8")
            soup = BeautifulSoup(content, "xml")
            # wrangle BDX data
            self.ingest(soup)

    def ingest(self, data_soup: Any) -> bool:
        """ingestion controller handles data wrangler loop (the magic ✨)"""
        # XML root
        masterplan = data_soup.find("Builders")
        # Company xml
        companies = masterplan.findChildren("Corporation", recursive=True)
        for company in companies:
            # Company data
            this_company = Company(company)
            # Builder xml
            builders = company.findChildren("Builder", recursive=False)
            for builder in builders:
                # Builder data
                this_builder = Builder(
                    builder,
                    company=this_company,
                    clientSlugs=self.client.WP_CPT_SLUG_ID,
                )
                # print( this_builder.name )
                # Subdivision xml
                subdivs = builder.findChildren("Subdivision", recursive=False)
                for subdiv in subdivs:
                    # Subdivision data
                    this_subdiv = Subdivision(
                        subdiv,
                        company=this_company,
                        builder=this_builder,
                        clientSlugs=self.client.WP_CPT_SLUG_ID,
                        filterList=self.client.NAME_FILTER_LIST,
                    )
                    # print( this_subdiv.name )
                    # Data relationships
                    this_builder.addRelationship(
                        "subdivs", this_subdiv.wp_cpt_id
                    )  # Builder Relationship
                    this_subdiv.addRelationship(
                        "builder", this_builder.wp_cpt_id
                    )  # Subdiv Relationship
                    # Plan xml
                    plans = subdiv.findChildren("Plan", recursive=False)
                    for plan in plans:
                        # Plan data
                        this_plan = Plan(
                            plan,
                            company=this_company,
                            builder=this_builder,
                            subdiv=this_subdiv,
                            clientSlugs=self.client.WP_CPT_SLUG_ID,
                            filterList=self.client.NAME_FILTER_LIST,
                        )
                        # Data relationships
                        this_builder.addRelationship(
                            "plans", this_plan.wp_cpt_id
                        )  # Builder-Plan Relationship
                        this_subdiv.addRelationship(
                            "plans", this_plan.wp_cpt_id
                        )  # Subdiv-Plan Relationship
                        this_plan.addRelationship(
                            "builder", this_builder.wp_cpt_id
                        )  # Plan-Builder Relationship
                        this_plan.addRelationship(
                            "subdiv", this_subdiv.wp_cpt_id
                        )  # Plan-Subdiv Relationship
                        # add PLAN to dataset
                        self.raw["plans"].append(this_plan)
                        self.json["plans"].append(this_plan.getDict())
                    # add SUBDIVISION to dataset
                    self.raw["subdivs"].append(this_subdiv)
                    self.json["subdivs"].append(this_subdiv.getDict())
                # add BUILDER to dataset
                self.raw["builders"].append(this_builder)
                self.json["builders"].append(this_builder.getDict())
        # return True after ingest func wrangles all datasets
        return True
