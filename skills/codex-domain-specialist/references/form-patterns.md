# Form Patterns

## Scope
Use when building complex forms: multi-step flows, dynamic fields, validation, and file inputs.

## React Hook Form (Recommended)

```jsx
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  firstName: z.string().min(1, "Required").max(100),
  lastName: z.string().min(1, "Required").max(100),
  email: z.string().email("Invalid email"),
  role: z.enum(["user", "admin", "manager"]),
  department: z.string().min(1, "Select a department"),
  skills: z
    .array(
      z.object({
        name: z.string().min(1),
        level: z.enum(["beginner", "intermediate", "expert"]),
      })
    )
    .min(1, "Add at least one skill"),
});

function UserForm({ defaultValues, onSubmit }) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting, isDirty },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: defaultValues || { skills: [{ name: "", level: "beginner" }] },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "skills" });

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <input className={`input ${errors.firstName ? "input-error" : ""}`} {...register("firstName")} />

      {fields.map((field, index) => (
        <div key={field.id}>
          <input className="input" {...register(`skills.${index}.name`)} />
          <select className="input" {...register(`skills.${index}.level`)}>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="expert">Expert</option>
          </select>
          <button type="button" onClick={() => remove(index)}>Remove</button>
        </div>
      ))}

      <button type="button" onClick={() => append({ name: "", level: "beginner" })}>Add Skill</button>
      <button type="submit" disabled={isSubmitting || !isDirty}>Save</button>
    </form>
  );
}
```

## Multi-Step Form

```jsx
function MultiStepForm() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({});
  const totalSteps = 3;

  const next = (stepData) => {
    setFormData((prev) => ({ ...prev, ...stepData }));
    setStep((s) => Math.min(s + 1, totalSteps));
  };

  const back = () => setStep((s) => Math.max(s - 1, 1));

  const submit = async (finalData) => {
    const complete = { ...formData, ...finalData };
    await api.post("/users", complete);
  };

  return (
    <div>
      {step === 1 && <PersonalInfoStep onNext={next} defaults={formData} />}
      {step === 2 && <EmploymentStep onNext={next} onBack={back} defaults={formData} />}
      {step === 3 && <ReviewStep data={formData} onBack={back} onSubmit={submit} />}
    </div>
  );
}
```

## Form UX Rules
- Show validation errors inline, per field.
- Validate on blur first, then on change after first error.
- Disable submit button while submitting.
- Preserve dirty form state and warn before leaving.
- Auto-focus first field when form opens.
- Use `noValidate` on `<form>` for controlled validation.
- Mark required fields clearly.
