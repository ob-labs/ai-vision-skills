# Verify that the selected GitHub release describes one immutable public product build.
def image($role): "^ghcr\\.io/antgroup/ai-vision/\($role)@sha256:[a-f0-9]{64}$";
.source_repository == "antgroup/ai-vision"
and .release_tag == $tag
and .product_version == $version
and .channel == $channel
and (.source_sha | type == "string" and test("^[a-f0-9]{40}$"))
and (.build_id | type == "string" and test("^[1-9][0-9]*\\.[1-9][0-9]*$"))
and (.images | type == "object" and keys == ["agentlens", "aivision-be", "aivision-fe", "antcollector-gw", "signoz-ob"]
    and (.agentlens | type == "string" and test(image("diagnosis")))
    and (.["aivision-be"] | type == "string" and test(image("backend")))
    and (.["aivision-fe"] | type == "string" and test(image("frontend")))
    and (.["antcollector-gw"] | type == "string" and test(image("ingest-gateway")))
    and (.["signoz-ob"] | type == "string" and test(image("data-backend"))))
