module.exports = {
	name: "saashq-ignore-asset",
	setup(build) {
		build.onResolve({ filter: /^\/assets\// }, (args) => {
			return {
				path: args.path,
				external: true,
			};
		});
	},
};
