from unittest import TestCase
from src import Plasmid, ArrowFeature


class TestArrowStyle(TestCase):

    def test_style(self):
        basic_plasmid = Plasmid("pBR322_1", 4361)

        # Adding features
        tcr = ArrowFeature("TcR", 86, 1276, style="publication")
        basic_plasmid.add_feature(tcr)

        ori = ArrowFeature("ori", 2534, 3122, direction=-1, style="narrow")
        basic_plasmid.add_feature(ori)

        ampr = ArrowFeature("ampr", 3293, 4153, direction=-1, style="major")
        basic_plasmid.add_feature(ampr)

        ampr_promoter = ArrowFeature("ampr promoter", 4154, 4258, direction=-1, style="promoter")
        basic_plasmid.add_feature(ampr_promoter)

        basic_plasmid.save_to_file("test_file")
    pass
