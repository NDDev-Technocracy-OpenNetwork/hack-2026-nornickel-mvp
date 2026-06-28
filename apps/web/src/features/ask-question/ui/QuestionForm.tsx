import { Search } from "lucide-react";
import { useState } from "react";

import { defaultQuestion } from "@/shared/i18n/ru";

type QuestionFormProps = {
  disabled?: boolean;
  onSubmit: (question: string) => void;
};

export function QuestionForm({ disabled, onSubmit }: QuestionFormProps) {
  const [question, setQuestion] = useState(defaultQuestion);

  return (
    <form
      className="question-form"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(question);
      }}
    >
      <textarea
        aria-label="Вопрос по материалу, режиму и свойству"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
      />
      <div className="button-row">
        <button className="primary-button" disabled={disabled} type="submit">
          <Search size={17} />
          Найти доказательства
        </button>
      </div>
    </form>
  );
}
