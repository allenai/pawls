import json
import shutil
from dataclasses import dataclass
from typing import Dict, List, OrderedDict

import pdfplumber as pp

EMAIL = "alyssa.j.page@gmail.com"


def struct_fn(sha: str) -> str:
    return f"./annotations_alyssa/sections-annotation/{sha}/pdf_structure.json"


def annots_fn(sha: str) -> str:
    return f"./annotations_alyssa/sections-annotation/{sha}/{EMAIL}_annotations.json"


def pdf_fn(sha: str) -> str:
    return f"./annotations_alyssa/sections-annotation/{sha}/{sha}.pdf"


def status_fn() -> str:
    return "annotations_alyssa/sections-annotation/status/{EMAIL}.json"


with open(status_fn(), encoding="utf-8") as f:
    status = json.loads(f.read())

completed_items = []
skip_shas = set(
    [
        # Batch 0
        "65b57ad4b975975b6d87fd4d147817ca1da2fc9e",
        "9b9f2d31890a33d57eaad959bcc5f51b463df162",
        "001534ec4e6d656722fddc81ba532779cea76875",
        "04a178c02ea7a0ee41550bcf750ab9690b799698",
        "050035080b5d6a2b11b127d0b9868c1d35a872d9",
        "09624d32cc4492dbd68706df020137ddf47d4554",
        "09c1bf59a0521a1533daa25fc38cebbc11541fbe",
        "0ae6f69b8ea34117ba7083c293405ddaba5b8f2b",
        "0b3c4723c5e5b34c1f512721900e542cb654d83a",
        "0c2093a26725d423654baa4f009e6c919cb8ca1e",
        "0c69b1e916476bbdd8b1b38bbb1aa877709a0f28",
        "0c974b236c8c2a3ed2c881866b546f14f3749005",
        "0cb52d6f316ab715e4d5898812153d1a81415463",
        "0cd1148b4a875a0ee6c0a4999a7e8f07e66ecbfe",
        "0ef3cc828e4ab9589107c5d0f1f20c31b4fb3b23",
        "0fbfea6bf315e9609bd2baf28c145b6390f8de1c",
        "105d22748b95384edd4fc0bcd07ee481d1611098",
        "10c8efb5a0cec40740e71ce20927950bc7f12807",
        "13b879be58bc89fd3abf945c83b18844022decc5",
        "158d4215081464510a5681a4442c087284e746ce",
        "1910ae59b83730acd2c82b2a0c52a8fe5563ce1a",
        "1959008518878ddb875062fa5a7079790a830a98",
        "1d6c94d1e742003cc7deb3fa6e12392225472dfa",
        "204a768859ad2f8ed85a9913cbb3c8e89f32285a",
        "20fdafb68d0e69d193527a9a1cbe64e7e69a3798",
        "21f95b703430a802b80c36ecd34dc30e73df59c4",
        "249623fe957042eebff9e95c16d0e33ff25037e3",
        "249d9a37789b0163e004973f1ed9b4daaea0e26a",
        "24be27b62e0355cf15182913cf3f1e4e0e17d4df",
        "264388650dec372765e74ac7f93c58ad056a6ba7",
        "268f9017be73961f9aa4f364e90af609f0dac4ca",
        "26ed89bff49545f8c6ddfd05ba9a9c59c926d322",
        "26edeff1028a4f11adc21ee2501a624219b1c969",
        "28d439b0f1fa2394a9a50cd251cf575a1a569391",
        "2ab6cd06b36cd42ddfa4f98427d8011f19eb8a1d",
        "2c33f2aed89a7b04c2509b897e5fcccccdb2b7b6",
        "2d76d1a18bec9f887e400905781041c311087a3e",
        "2dff68593de2607b05aa57f91861014bc71ae228",
        "2e4281cf4d1565971450f7a96c87e961a7ca648b",
        "2e6b8bcbc0d3434a4edc233466b5b3fa42e6d5aa",
        "2fb4de3d12a46dadbbd10d0d6410d645d14444c2",
        "304e2a42e897aa728d394e2d1e60ea26f4f1c101",
        "311a185718716b56d9a3dff3bd4a96d2bab1a19a",
        "335ab0ef648562cf9c35ffb25b0169fd14327502",
        "33c8f4ed9c1f247b97506f964ae06d49f9b2b7d2",
        "348a852a6cd58d1500aa81789b4fc1e8452a087e",
        "36909e01d9f51870068521562e107289aeb5bd34",
        "36ac62e68d60d79e572d635e86725ee92bb5f43a",
        "376c3d068c61292bd4f74e4499104ff8856d8d56",
        "38223d930125c139670402c99bb10ab2ae0ab94f",
        # Batch 1
        "3ccc4c2f77569913c83092f793a44a764e8d3a21",
        "3ee2d3154675c0d09ecd72710d0910ad8d79ca19",
        "3f7fae7ace36c562158c2e9b24f02d824f4a203c",
        "406d696e01cf94f0fa181042324c760bc958e85d",
        "406f70bda890ca25a48e53a41640eabdb0507378",
        "42943647fca7b474957640b014ef5af984689bec",
        "42ab2e42221a7fbd66ba368cf90b5e63b5270010",
        "43d93cecfe673319c71d43d40cc9379d54b460f4",
        "46244ddd0210fe70cff66360171b271319ec9090",
        "47d9133629a7dee1664483944547658e8cea83f2",
        "488b0342811f882a720f963f10eb038b5d62857d",
        "492184ec062f59a03209b0d39693d79f4262fbb2",
        "4be952924cd565488b4a239dc6549095029ee578",
        "4c471de482b20f6d942da38b1c97aff7720db658",
        "4c8c2cbdf4c12cb810a64a8cfc9ef88c1d5df059",
        "4d77d2b67ab351a5a041cdf003274ddcf7970389",
        "4ecb8bc1d3da10745a47895e109009c5eac81ce3",
        "4f7f513751019ada20f9f9e979cee7a9923459fa",
        "51517d5d900a7c0cd33e210c48cb27ef3b96e5a9",
        "548190ff2a3a42f2f05480fd2b6f14b47fe02df4",
        "55769ebfb0f1d5541ec7d6bc5d998b4be0f511d3",
        "5909ff87cf05db435930a55e1a9cf5e0a435115e",
        "59aac9b863772d682b6b47a11c93ac0518c5a0f3",
        "5aa639083e98513e8a08cd32ca0358ef98434093",
        "5b0f61e0af7abf2c54b6601d8c40a69f09b49823",
        "5ba64e4221a4c018e0e84ab1330a0ad69f999cb9",
        "5d81ef4cfef4e0977c7d26990daa7976cd3561b6",
        "5e2cb2857c696a1dac92b80db8b67f4331caa143",
        "6043abe49bdfcbcae030ec7499eb369719eb3bcd",
        "608ebdf2aa88864bcd6aa95beda6027ca4c14874",
        "61f1ac16610fcc20ba49432aa7a5943ad5b7fdd8",
        "63fe97196a49b00b88278cea7aa0cc55fa0e32e7",
        "640aa39bff0d5a5cd2c7e5ab7a1972531c612e2a",
        "64b7ba8f61234700147b827a6a0c5df6fe893257",
        "64d1901319f2a36c9b57c18ff818d18abbb7f204",
        "64fddc494443639a4c513e9fbddb9363e999a368",
        "65dc6f20f4bbc357f2ccfd1361855862e54b97e6",
        "6a884dcf19c60c46bf3a32306b3375bcaa6baa18",
        "6b5cc3a5089feb614f19609876112686ac1a61ac",
        "6d9c17750b75f77ec2498da935d1631c95515f68",
        "6df386f95e548388efc73b4ac304afb65c4ec81d",
        "6dfb928fdb35958303687b277c12d9e244229476",
        "6eb12a379cdd625fd3d2e7428548f5b782cc8660",
        "6eb5c3db983399064f04f2d6680a280b0cb028cb",
        "71923169d936faf61e2918e0e6d4397513c22621",
        "71a11496bc0d1e680d29e7a5228299201c4a03e7",
        "770c74cbc615e299f541075677b56d088e133aa3",
        "78b0633e2d1ae35f393b7b5667e59370d3cb2a11",
        "79371f3b707c79bee603b278cafb76a5e45b9ade",
        "7a0720a9a06d449384ac6ca2e1780e5b8fdb93b8",
        # Batch 2
        "348a852a6cd58d1500aa81789b4fc1e8452a087e",
        "3f7fae7ace36c562158c2e9b24f02d824f4a203c",
        "42ab2e42221a7fbd66ba368cf90b5e63b5270010",
        "5909ff87cf05db435930a55e1a9cf5e0a435115e",
        "5aa639083e98513e8a08cd32ca0358ef98434093",
        "6dfb928fdb35958303687b277c12d9e244229476",
        "7bfe505e8fb5be23b3c639a6a916454e322e3c81",
        "7f0c48a4557b5f223ae120f933a973c671ed2078",
        "7f73791468bdbb814480092fe5eabf73599629d0",
        "7fea93c09706ee51919ae963195974f9c0882c42",
        "81383d841a47f654f6afec33947e6ad8f9fce6f9",
        "819724765844c625b7ab701783770ffd102a1ad2",
        "82a4233b97a226c666e5a25f9c2e0296d95a90a0",
        "830973ec4517182eb43ed94526b8399650989d7a",
        "836ca47a898db02e2e3bc214f1ac2d163535b945",
        "838650ed2aa132ab2d9927e81e60e273a8357cf5",
        "84f792bc446e47acf47ab00de0713a7c4e2ec686",
        "8527f41495fd2cd40fb80ba8efc8ba6b42a9ba88",
        "88ac26bfaadaaadfc6ffca275f2c67fbf8137d17",
        "88c5612b48e1e61f1c4795734968bd09b37afd95",
        "8962f495d9beca16c60877ed7175a6befb083d91",
        "8b479fa4ddca33db722c89646a44cdfd065ebdf2",
        "8b7dbf3b88bce56d08bd37bc318141638a3dfece",
        "8c21b058944f42f0386a7e5e49206beb8e2350d0",
        "8caa0744cb4a4d967ec743d89389adbe4e1ae03e",
        "8d6a348c4b00da0c30f9f5c77619ea40e441652b",
        "90f074a9f74c0c6956963855bd45f92853fcf287",
        "9249db2228378050edb6c6a70488f033f0c3f992",
        "92a6b83111e38829c3cd388bc468c40220c48355",
        "946a170bfdc8ff6bc35537f101f72cbc6d535660",
        "961e9a7a22bb6bf6fd2f5d181b541bb2d519dbfd",
        "96e3b047b173c16bdaa44b990d4aa284676b7f0f",
        "99fc26c55a01d010ec39c8e0ee78fdb4788fbc9b",
        "9a47f4807d734da978d7f774f4a3df8ae9ae62aa",
        "9a81b5aed97d222b2506357fce41b3a9651e0ab5",
        "9b71542ef5d5178041048b9a330309053bb0bcfc",
        "9b79eb8d21c8a832daedbfc6d8c31bebe0da3ed5",
        "9ce08cb604bb23531c61516c0c50eed6dcb4524f",
        "a0ab145f170c64c5db3b746d84f2688cb9d77b24",
        "a0d5bf4740679e4b5d15869f89b3e37218c42eac",
        "a4beb55e1a30399e482258cb963bf2e5c22f5a46",
        "a7599c40b1d99bb0c780f0d76495eff44230bf52",
        "a77e20cefc38a92599ef83d362e6fbc6ca9f9323",
        "a821453809f36a23402ce93b6042c76d85a720a6",
        "a8a5cb9e2ab60abc6ab55601c2a2ea9c9e6a8218",
        "aab4da087d75eceb058cdd49250c9a6b9aae0b07",
        "b010ef9d5b1bc09b6cae4b94144b8334173d1f86",
        "b137e00abe03aaef1a6738bb3e73435c682ab4f8",
        "b190ea932d22c73694e00b4e7610e60cf779ab85",
        "b257e1ecdf123d54a37ad07eb2bfb02bc0f10dff",
        "b35dd2a3850667b6b7a0e8dfb3ef03ca463bcd18",
        "b368aa6eb6cd0389e8d95a8533b1a5c60df2b00b",
        "b381e7368b6726c6801e1d4ccf7cb2306c382f0a",
        "b458de039bb6171352570182248a71a7dede8066",
        "b483aec9de713789319bec400e09f116bb7f830b",
        "b4b212764e2e633c3f16d33ff1cd8363afbf9c01",
        # Batch 3
        "6dfb928fdb35958303687b277c12d9e244229476",
        "8c21b058944f42f0386a7e5e49206beb8e2350d0",
        "b381e7368b6726c6801e1d4ccf7cb2306c382f0a",
        "bbda1a954707ac6851b3f0d8eaf643432dd9280b",
        "bdc574098729f4c4edfde53d5f22a71a76820210",
        "be93ad3c103b390e1e432b1fd72c5f01eea0495e",
        "bef346fcc85ad3ccfcf7fa6bfe3ef96ebd782b4f",
        "bfdcf135b86832a708a460eb1fe9d4c40900cd3e",
        "c03719e982c3a28d3e604db1630fc79bfde214c6",
        "c04d01cb56526d932f07dc63a2baa166dcfee218",
        "c0f59a59c0acd5dfcb6b88d7418be0b93118db47",
        # "c11fc5960034a458d24d3ee2e07d8154a3df5d58",
        "c142d11d4d8178771f67f61dab5d45c955e8ba1f",
        "c353c5f63d16c6e824bf6e488a433d660deada22",
        "c35bfaf0b1e29d4b7b92106a15d0d0b50860cd2a",
        "c577aa008350f3bd8af30496755765ba086d065e",
        "cbb6fd90710f7df0ef9211ea56c419895efa3bd5",
        "cc098f63821cc9918588cefee12158ce1552b373",
        "cc52a200a2e3355d52550d1e42414fc787eba553",
        "cd803b52ea93f03d07cdf9a9cc286136e1e29177",
        "ce3df60e3489b324a4431eab1e5e4e35813af716",
        "ce9e561a9c58b250669bd6ee4b602421809c2c99",
        "cf596696350256ce42933835121118e56bc8232e",
        "d0c86c231bedd954114e715601c075646e289878",
        "d29c1e3f0e1f1b6d52ce00c4c1cbd35e48d787f3",
        "d29cf4df3d0380e86263368c4eb69394ebbf8eb7",
        "d3c364545f66a59cd344dd7628084dba0bff1eba",
        "d587b7e8ad11c7f26cc9282b3a73af7dd2c70002",
        "d7613677ea88004ec2c200d981fd750f0ff03bed",
        "d854563c380252a76f293786c17b28d6debe0cb9",
        "d94fd1f59cca0500dbc93593d118294700a6848c",
        "d97c464c24e6bfde166a09e05df303f38ca3ba0b",
        "d9b146cc7444d4aa68136366e929d8c76b809b5e",
        "dacb4aa3ebde69ef47fed1a1d355f01921f7c16f",
        "dd56319cf6dc7c6e7608a36f691389d68e6b3956",
        "df0f8d9dd295715972f75151b7ca7fab2748d9d8",
        "e0fe3e9fbc51365258192eae645a55c5ca6b32dd",
        "e1edcef40030babf339647e2c5d378ecb3cf1a1b",
        "e39f994c5c0ec5b6a4a633295dd67bd71eb014e7",
        "e68b0ea5857a25504bb13f06797db007183779b0",
        "e84c1e92f10e00bcd0cbc96ba3f6064c8cae9ed2",
        "e8c7d901cf569d6e224591494e184b20827350db",
        "eaa33bb2ac72693edacf83ca0f7d4174110a153e",
        "ec5574732e8d45afa5b8221607e61769b4a3e9d6",
        "f0f91fb247bcbb973ab360d754c32c7c5686798f",
        "f1b7d3a5a94aca969c07d72f8ec4e4f0909d125f",
        "f553762e8a22aeda384bd8c0c19cc83e409a2113",
        "f6e9c799b32b3e75b3485d7c2a3723bbf1a85c72",
        "fa9d81ef8758457537d516761ae37dbfed6ed95c",
        "faf8abf19a89fa0e40f3f50550816a3bdecb80f0",
        "fe205a569ce976b8856ddb8c8000d34a7ccf803a",
        "fe9a76c66b4f9b5cd3f49c87e6995d10a394e45e",
        "ff51f2a18232276c6729bb198990b0951ae474db",
    ]
)

for sha, item in status.items():
    if item["finished"] and sha not in skip_shas:
        completed_items.append(sha)


@dataclass
class Box:
    x: float
    y: float
    width: float
    height: float


@dataclass
class Relation:
    target_ids: List[str]


@dataclass
class Token:
    text: str
    box: Box


@dataclass
class Annotation:
    id: str
    page: int
    label: str
    tokens: List[Token]


for sha in completed_items:
    with open(struct_fn(sha), encoding="utf-8") as f:
        structure = json.loads(f.read())

    page_to_tokens: Dict[int, List[str]] = {}

    for s in structure:
        page, tokens = s["page"], s["tokens"]
        page_to_tokens[page["index"]] = [
            Token(text=t["text"], box=Box(t["x"], t["y"], t["width"], t["height"]))
            for t in tokens
        ]

    with open(annots_fn(sha), encoding="utf-8") as f:
        annots = json.loads(f.read())

    id_to_annot: Dict[str, Annotation] = OrderedDict()

    for annot in annots["annotations"]:

        # Custom bounding box (manual annotation)
        if not annot["tokens"]:
            with pp.open(pdf_fn(sha)) as pdf:
                target_page = pdf.pages[annot["page"]]
                target_box = (
                    annot["bounds"]["left"],
                    annot["bounds"]["top"],
                    annot["bounds"]["right"],
                    annot["bounds"]["bottom"],
                )
                target_words = target_page.crop(target_box).extract_words(x_tolerance=2)

                annot_tokens = [
                    Token(
                        text=t["text"],
                        box=Box(
                            t["x0"], t["top"], t["x1"] - t["x0"], t["bottom"] - t["top"]
                        ),
                    )
                    for t in target_words
                ]

        else:
            annot_tokens = [
                page_to_tokens[t["pageIndex"]][t["tokenIndex"]] for t in annot["tokens"]
            ]

        id_to_annot[annot["id"]] = Annotation(
            id=annot["id"],
            page=annot["page"],
            label=annot["label"]["text"],
            tokens=annot_tokens,
        )

    relations: Dict[str, List[str]] = {}

    for relation in annots["relations"]:
        for target_id in relation["targetIds"]:
            relations[target_id] = relation["targetIds"]

    # Skip these items b/c we already consumed them in a relationship
    consumed_for_relations = set()

    curr_id: int = 0

    # Move PDF for easy zipping later
    shutil.copy(pdf_fn(sha), f"./annotations_alyssa/pdfs/{sha}.pdf")

    with open(f"./annotations_alyssa/txts/{sha}.txt", "w", encoding="utf-8") as f:

        for _id, annot in id_to_annot.items():
            if _id in consumed_for_relations:
                continue

            if _id in relations:
                tokens = []

                for target_id in relations[_id]:
                    consumed_for_relations.add(target_id)
                    tokens.extend(id_to_annot[target_id].tokens)

            else:
                tokens = annot.tokens

            f.write(str(curr_id))
            f.write(" ")
            f.write(" ".join(map(lambda t: t.text, tokens)))
            f.write("\n")

            curr_id += 1
