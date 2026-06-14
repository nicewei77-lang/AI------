import {useState} from "react";
import type {FormEvent} from "react";
import type {NewPost} from "../types/post";

interface ProjectFormProps {
    onSubmit: (input: NewPost) => void | Promise<void>;
    submitting?: boolean;
}

function ProjectForm({onSubmit, submitting = false}: ProjectFormProps) {
    const [title, setTitle] = useState("");
    const [body, setBody] = useState("");
    const [oneLiner, setOneLiner] = useState("");
    const [serviceUrl, setServiceUrl] = useState("");
    const [githubUrl, setGithubUrl] = useState("");
    const [targetUser, setTargetUser] = useState("");
    const [techStackText, setTechStackText] = useState("");

    function handleSubmit(e: FormEvent) {
        e.preventDefault();
        const techStack = techStackText
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);

        void onSubmit({
            title: title.trim(),
            body: body.trim(),
            postType: "project",
            serviceUrl: serviceUrl.trim() || undefined,
            githubUrl: githubUrl.trim() || undefined,
            oneLiner: oneLiner.trim() || undefined,
            targetUser: targetUser.trim() || undefined,
            techStack,
            tags: [],
        });
    }

    const disabled =
        submitting ||
        !title.trim() ||
        !body.trim() ||
        !oneLiner.trim() ||
        !serviceUrl.trim();

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="mb-1 block text-sm font-semibold text-stone-800" htmlFor="title">
                    프로젝트명
                </label>
                <input
                    id="title"
                    required
                    className="w-full rounded border border-stone-300 px-3 py-2 text-sm outline-none focus:border-orange-400"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                />
            </div>

            <div>
                <label className="mb-1 block text-sm font-semibold text-stone-800" htmlFor="oneLiner">
                    한 줄 소개
                </label>
                <input
                    id="oneLiner"
                    required
                    className="w-full rounded border border-stone-300 px-3 py-2 text-sm outline-none focus:border-orange-400"
                    value={oneLiner}
                    onChange={(e) => setOneLiner(e.target.value)}
                />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
                <div>
                    <label className="mb-1 block text-sm font-semibold text-stone-800" htmlFor="serviceUrl">
                        서비스 URL
                    </label>
                    <input
                        id="serviceUrl"
                        type="url"
                        required
                        className="w-full rounded border border-stone-300 px-3 py-2 text-sm outline-none focus:border-orange-400"
                        value={serviceUrl}
                        onChange={(e) => setServiceUrl(e.target.value)}
                    />
                </div>
                <div>
                    <label className="mb-1 block text-sm font-semibold text-stone-800" htmlFor="githubUrl">
                        GitHub URL
                    </label>
                    <input
                        id="githubUrl"
                        type="url"
                        className="w-full rounded border border-stone-300 px-3 py-2 text-sm outline-none focus:border-orange-400"
                        value={githubUrl}
                        onChange={(e) => setGithubUrl(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
                <div>
                    <label className="mb-1 block text-sm font-semibold text-stone-800" htmlFor="targetUser">
                        타깃 사용자
                    </label>
                    <input
                        id="targetUser"
                        className="w-full rounded border border-stone-300 px-3 py-2 text-sm outline-none focus:border-orange-400"
                        value={targetUser}
                        onChange={(e) => setTargetUser(e.target.value)}
                    />
                </div>
                <div>
                    <label className="mb-1 block text-sm font-semibold text-stone-800" htmlFor="techStack">
                        기술 스택
                    </label>
                    <input
                        id="techStack"
                        className="w-full rounded border border-stone-300 px-3 py-2 text-sm outline-none focus:border-orange-400"
                        value={techStackText}
                        onChange={(e) => setTechStackText(e.target.value)}
                    />
                </div>
            </div>

            <div>
                <label className="mb-1 block text-sm font-semibold text-stone-800" htmlFor="body">
                    프로젝트 설명
                </label>
                <textarea
                    id="body"
                    required
                    className="min-h-40 w-full rounded border border-stone-300 px-3 py-2 text-sm leading-6 outline-none focus:border-orange-400"
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                />
            </div>

            <button
                className="rounded bg-stone-900 px-4 py-2 text-sm font-semibold text-white hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-stone-300"
                type="submit"
                disabled={disabled}
            >
                {submitting ? "등록 중..." : "프로젝트 등록"}
            </button>
        </form>
    );
}

export default ProjectForm;
